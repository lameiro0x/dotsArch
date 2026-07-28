#!/usr/bin/env python3
"""
wsctx — workspace context for Waybar / Hyprland.

Renders, per workspace, what is actually happening in it: the repo a Claude Code
session is working on and whether that session is waiting for you, the site a
browser is showing, the file tree an editor is in.

Design notes that are not obvious from the code:

  * This runs as a systemd --user service, NOT as a Waybar `exec` child. Waybar
    kills its exec children with killpg(SIGTERM) and then waitpid()s without a
    timeout, so a child that is slow to die freezes the whole bar; and any exec
    line containing a pipeline or a redirect leaks orphans on every bar reload.
    Staying outside that parent/child relationship avoids both.

  * State is published as one pre-rendered file per (output, workspace) pair, so
    the Waybar side is a bare `cat` rather than an interpreter start-up.

  * Claude Code's spinner rewrites the window title roughly once a second,
    forever, even when idle. That is ~4 Hyprland events per second with nothing
    happening. Debouncing alone does not help much; deduplicating the *rendered*
    output does, because the spinner never changes what we draw.

  * The braille spinner frames and U+2733 that Claude Code puts in the title do
    not exist in JetBrainsMono Nerd Font. Forwarding them drags in a fallback
    font (including a colour emoji font) and renders as specks. They are
    stripped, and session state is read from the session file instead.
"""

from __future__ import annotations

import json
import os
import re
import selectors
import signal
import socket
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

# ── Tunables ────────────────────────────────────────────────────────────────

DEBOUNCE_MS = 60          # coalesce an event burst into one render
SIGNAL_NUM = 9            # waybar listens on SIGRTMIN+9
HEARTBEAT_S = 30          # re-render even without events, to catch missed state
# The label length is shared by every slot on an output, focused or not. Letting
# the focused slot hold more text than the others means changing workspace
# changes widths, and every label to its right slides; equal lengths make focus a
# pure change of colour, so the easing is actually visible.
#
# It shrinks as an output fills up, because eight occupied slots at fourteen
# characters would be ~1330px and swallow the bar. Keyed on how many slots are
# occupied, so it only ever changes when a workspace gains or loses its last
# window — never on focus, never when a browser retitles a tab.
LABEL_BY_LOAD = {0: 14, 1: 14, 2: 14, 3: 14, 4: 14, 5: 13, 6: 11, 7: 9}
LABEL_MIN = 8

MAX_WS = 11  # 1-8 on the laptop, 9-11 on the external monitor


def label_width(occupied: int) -> int:
    return LABEL_BY_LOAD.get(occupied, LABEL_MIN)

# Material Design glyphs, which is the family the rest of this bar already
# speaks (see the `rewrite` map in config.jsonc). Measured at 13px in
# JetBrainsMono Nerd Font, every one of these advances 11px and inks 14-16px:
# a uniform set, which the mixed Nerd Font families are not — Font Awesome and
# Octicons overshoot the baseline and collide with the next character.
ICON_CLAUDE = "\U000F1719"   # md-robot-outline
ICON_TERM = "\U000F035B"     # md-memory, already meaning "kitty" in this bar
ICON_NVIM = "\U000F0577"
ICON_CODE = "\U000F0A1E"
ICON_FILES = "\U000F024B"
ICON_CHROME = "\U000F02AF"
ICON_FIREFOX = "\U000F0239"
ICON_WINDOW = "\U000F0379"   # md-monitor, the fallback

# Only the v2 events. The v1 variants double the event rate and v1 `windowtitle`
# does not even carry the title.
WATCHED = {
    "workspacev2", "focusedmonv2", "activewindowv2",
    "openwindow", "closewindow", "movewindowv2", "windowtitlev2",
    "createworkspacev2", "destroyworkspacev2",
    "monitoraddedv2", "monitorremoved", "urgent", "activespecialv2",
    "configreloaded",
}

CJK = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六",
       7: "七", 8: "八", 9: "九", 10: "十", 11: "十一"}

# Tints. Kept in lockstep with style.css; every value here is >= 3:1 against the
# pill background, which #585858 (the old inactive workspace colour) was not.
INK = "#c8c8c8"           # a label on the dark pill
INK_DIM = "#6a6a6a"       # the key column and icon on the dark pill
INK_BUSY = "#909090"      # the icon of a session that is working
INK_ON_WHITE = "#080808"  # a label on the active white pill
DIM_ON_WHITE = "#555555"  # the key column and icon on the active white pill

SESSIONS = Path.home() / ".claude" / "sessions"
SHELLS = {"fish", "bash", "zsh", "sh", "dash"}

# Anything Claude Code animates into the title. Stripped before display.
SPINNER = re.compile(r"[⠀-⣿✳✲✻·•]+")


# ── Hyprland IPC ────────────────────────────────────────────────────────────

def his() -> str | None:
    """The instance signature, re-read every time.

    It changes on every Hyprland restart and on every Hyprland upgrade, so
    caching it at start-up is how a long-running listener ends up talking to a
    socket that no longer exists.
    """
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if sig:
        # The directory surviving is not enough: a compositor that was killed
        # leaves the whole directory, sockets included, behind. Requiring the
        # control socket is what stops the daemon pinning itself to a dead
        # instance and never noticing the live one.
        if (Path(runtime_dir()) / "hypr" / sig / ".socket.sock").exists():
            return sig
    root = Path(runtime_dir()) / "hypr"
    if not root.is_dir():
        return None
    cands = [p for p in root.iterdir() if (p / ".socket.sock").exists()]
    if not cands:
        return None

    def mtime(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except OSError:
            return 0.0

    newest = max(cands, key=mtime)
    os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = newest.name
    return newest.name


def runtime_dir() -> str:
    return os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"


def sock_path(name: str) -> Path | None:
    sig = his()
    return Path(runtime_dir()) / "hypr" / sig / name if sig else None


def ask(command: str):
    """One request on the control socket, opened and closed each time.

    Holding this socket open blocks the compositor for five seconds per
    request, because its accept loop is synchronous.
    """
    p = sock_path(".socket.sock")
    if p is None:
        return None
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(str(p))
            s.sendall(command.encode())
            chunks = []
            while True:
                b = s.recv(65536)
                if not b:
                    break
                chunks.append(b)
        return json.loads(b"".join(chunks) or b"null")
    except (OSError, ValueError):
        return None


# ── /proc resolution ────────────────────────────────────────────────────────

def children_of(pid: int) -> list[int]:
    try:
        raw = Path(f"/proc/{pid}/task/{pid}/children").read_text()
    except OSError:
        return []
    return [int(x) for x in raw.split()]


def comm_of(pid: int) -> str:
    try:
        return Path(f"/proc/{pid}/comm").read_text().strip()
    except OSError:
        return ""


def stat_fields(pid: int) -> list[str] | None:
    """/proc/<pid>/stat, split so a comm containing spaces or parens is safe."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return None
    close = raw.rfind(")")
    if close == -1:
        return None
    return ["", ""] + raw[close + 2:].split()


def cwd_of(pid: int) -> str | None:
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return None


def foreground_of(shell_pid: int) -> int | None:
    """The pid group holding the terminal, i.e. what the user is actually running.

    Field 5 is pgrp and field 8 is tpgid; when they differ, something is running
    in the foreground and tpgid identifies it.
    """
    f = stat_fields(shell_pid)
    if not f or len(f) < 9:
        return None
    try:
        pgrp, tpgid = int(f[4]), int(f[7])
    except ValueError:
        return None
    if tpgid <= 0 or tpgid == pgrp:
        return None
    return tpgid


def shell_under(term_pid: int) -> int | None:
    """The shell inside a terminal window.

    The first child of a kitty window is a `kitten` helper whose cwd is $HOME —
    taking it would label every terminal with the home directory.
    """
    queue, seen = list(children_of(term_pid)), set()
    while queue:
        pid = queue.pop(0)
        if pid in seen:
            continue
        seen.add(pid)
        if comm_of(pid) in SHELLS:
            return pid
        queue.extend(children_of(pid))
    return None


def claude_session(pid: int) -> dict | None:
    """The session file Claude Code keeps for a live session, if this is one.

    Undocumented, so every field is treated as optional and a malformed or
    half-written file is simply a miss.
    """
    f = SESSIONS / f"{pid}.json"
    try:
        data = json.loads(f.read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    # Guard against pid reuse: procStart must match the kernel's start time.
    want = str(data.get("procStart", "")).strip()
    if want:
        st = stat_fields(pid)
        # Fail closed. If the process is gone the file is a leftover — those
        # are not pruned — and trusting it would label a workspace with the
        # repo of a session that ended.
        if st is None or len(st) <= 21 or st[21] != want:
            return None
    return data


# ── Labelling ───────────────────────────────────────────────────────────────

def strip_spinner(s: str) -> str:
    return SPINNER.sub("", s).strip()


#  Cc control, Cf format, Cs surrogate, Zl/Zp line and paragraph separators.
#  Deliberately NOT Co: Nerd Font icons live in the private use area, and
#  dropping that category silently erases every glyph in this bar.
_DROP = {"Cc", "Cf", "Cs", "Zl", "Zp"}


def safe(s: str) -> str:
    """Printable and Pango-safe."""
    s = "".join(ch for ch in s if unicodedata.category(ch) not in _DROP)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clip(s: str, n: int, middle: bool = True) -> str:
    """Clip to n characters, from the middle by default.

    Head truncation is the wrong default for this machine: the repo names share
    prefixes (`lameiro0x`, `lameiro0x-site`, `lameiro0x.github.io`;
    `pentest-recon-toolkit`, `pentesting-path-htb`), so cutting the tail throws
    away the only distinguishing part. Trailing separators are stripped too,
    because `github.` + `…` reads as a typo rather than as a truncation.
    """
    s = s.strip()
    if len(s) <= n:
        return s
    if not middle:
        # Prose reads left to right; a sentence keeps its head.
        return s[: n - 1].rstrip(" ._-/") + "…"
    head = (n - 1) // 2 + (n - 1) % 2
    tail = (n - 1) - head
    return s[:head].rstrip(" ._-/") + "…" + s[len(s) - tail:].lstrip(" ._-/")


BROWSERS = {
    "chromium": (ICON_CHROME, re.compile(r"\s+-\s+Chromium$")),
    "google-chrome": (ICON_CHROME, re.compile(r"\s+-\s+Google Chrome$")),
    "firefox": (ICON_FIREFOX, re.compile(r"\s+[—-]\s+Mozilla Firefox$")),
    "zen": (ICON_FIREFOX, re.compile(r"\s+[—-]\s+Zen( Browser)?$")),
    "brave-browser": (ICON_CHROME, re.compile(r"\s+-\s+Brave$")),
}
TERMINALS = {"kitty", "alacritty", "foot", "wezterm"}
EDITOR_COMMS = {"nvim": ICON_NVIM, "vim": ICON_NVIM,
                "hx": ICON_NVIM, "emacs": ICON_NVIM}


def describe(client: dict) -> tuple[str, str, str]:
    """(class column, label, state) for one window."""
    cls = (client.get("class") or "").lower()
    title = strip_spinner(client.get("title") or "")
    pid = client.get("pid") or 0

    if cls in BROWSERS:
        tag, suffix = BROWSERS[cls]
        return tag, suffix.sub("", title) or "browser", ""

    if cls in TERMINALS:
        shell = shell_under(pid)
        if shell is None:
            return ICON_TERM, "shell", ""
        fg = foreground_of(shell)
        if fg:
            sess = claude_session(fg)
            if sess and sess.get("cwd"):
                status = str(sess.get("status") or "")
                return ICON_CLAUDE, Path(sess["cwd"]).name, status
            comm = comm_of(fg)
            icon = EDITOR_COMMS.get(comm, ICON_TERM)
            here = cwd_of(fg) or cwd_of(shell)
            return icon, (Path(here).name if here else comm), ""
        here = cwd_of(shell)
        return ICON_TERM, (Path(here).name if here else "shell"), ""

    if cls in ("code", "code-oss", "vscodium"):
        return ICON_CODE, title.replace(" - Visual Studio Code", ""), ""
    if cls in ("thunar", "nautilus", "org.gnome.nautilus"):
        return ICON_FILES, title, ""

    return ICON_WINDOW, (title or cls or "window"), ""


# ── Rendering ───────────────────────────────────────────────────────────────

def render(entry: dict | None, wsid: int, active: bool, width: int = 12) -> dict:
    if entry is None:
        return {
            "text": CJK.get(wsid, str(wsid)),
            "tooltip": "",
            "class": ["empty"] + (["active"] if active else []),
        }

    tag, label, state, tip = (
        entry["tag"], entry["label"], entry["state"], entry["tooltip"],
    )

    waiting = state == "waiting"
    working = state == "busy"

    # Padded to a fixed cell count rather than clamped with CSS `min-width`.
    # GTK3 has no `text-align`, so a wider box just centres a short label and
    # the numerals stop forming a column — which is the whole point of a
    # ledger. Padding the string instead makes every slot identical in width
    # AND left-aligned, so a browser tab changing its title moves nothing.
    body = safe(clip(label, width).ljust(width))
    inkc = INK_ON_WHITE if active else INK
    if active:
        keyc = iconc = DIM_ON_WHITE
    else:
        keyc = INK_DIM
        # A working session warms its icon one step. This has to happen in the
        # markup: a CSS rule cannot win against a Pango span that already
        # names a colour, which is why the earlier `.working` stylesheet rule
        # was dead.
        iconc = INK_BUSY if working else INK_DIM

    # The workspace number is the key column. It is what makes this a ledger
    # rather than a run-on line, and it is the actionable half of the answer:
    # the bindings are Ctrl+1..8 (hyprland.conf), so a row that says which
    # workspace holds a repo is worth more than one that only says it exists.
    text = (
        f'<span foreground="{keyc}">{wsid}</span> '
        f'<span foreground="{iconc}">{safe(tag)}</span> '
        f'<span foreground="{inkc}">{body}</span>'
    )

    classes = ["occupied"]
    if active:
        classes.append("active")
    if waiting:
        # Drawn by the stylesheet as a ring around the whole pill. A glyph
        # cannot carry this: a bullet is ~7px of ink competing with 2500px of
        # white pill, and on the active slot it would be white on white.
        classes.append("waiting")
    if working:
        classes.append("working")

    return {"text": text, "tooltip": tip, "class": classes}


def collect() -> dict | None:
    clients = ask("j/clients")
    monitors = ask("j/monitors")
    workspaces = ask("j/workspaces")
    rules = ask("j/workspacerules")
    if clients is None or monitors is None or workspaces is None:
        return None

    active_ws = {}
    ws_output = {}
    outputs = []
    for m in monitors:
        name = m.get("name")
        if not name:
            continue
        outputs.append(name)
        aw = (m.get("activeWorkspace") or {}).get("id")
        if aw is not None:
            active_ws[name] = aw

    # The workspace rules are authoritative and, unlike the live workspace list,
    # they still describe workspaces belonging to a monitor that is unplugged.
    for r in rules or []:
        try:
            wsid = int(str(r.get("workspaceString", "")).strip())
        except ValueError:
            continue
        if wsid > 0 and r.get("monitor"):
            ws_output[wsid] = r["monitor"]

    for w in workspaces:
        if isinstance(w.get("id"), int) and w["id"] > 0:
            ws_output.setdefault(w["id"], w.get("monitor") or "")

    # Windows a user cannot see should not describe a workspace.
    by_ws: dict[int, list[dict]] = {}
    for c in clients:
        ws = (c.get("workspace") or {}).get("id")
        if not isinstance(ws, int) or ws <= 0:
            continue
        if not c.get("mapped", True) or c.get("hidden", False):
            continue
        by_ws.setdefault(ws, []).append(c)

    entries: dict[int, dict] = {}
    for ws, wins in by_ws.items():
        wins.sort(key=lambda c: c.get("focusHistoryID", 1 << 30))
        tag, label, state = describe(wins[0])
        lines = []
        for w in wins:
            t, l, s = describe(w)
            mark = {"waiting": "  · esperando",
                    "busy": "  · trabajando"}.get(s, "")
            # Waybar hands the tooltip to set_tooltip_markup, so it needs the
            # same escaping the label gets. An unescaped "Tom & Jerry" breaks
            # the tooltip outright, and "<b>" in a page title would be obeyed.
            lines.append(f"{safe(t)}  {safe(l)}{mark}")
        entries[ws] = {
            "tag": tag, "label": label, "state": state,
            "extra": len(wins) - 1,
            "tooltip": "\n".join(lines),
        }

    # The focused window per output, for the left island. Doing it here rather
    # than with Waybar's `rewrite` is not a preference: that option runs
    # std::regex over raw bytes, so a character class written with non-ASCII
    # codepoints becomes a byte range and eats the leading letter of any
    # accented title — "École" renders as "cole".
    focused: dict[str, str] = {}
    for out in outputs:
        wsid = active_ws.get(out)
        wins = by_ws.get(wsid or -1, [])
        if not wins:
            continue
        top = min(wins, key=lambda c: c.get("focusHistoryID", 1 << 30))
        focused[out] = strip_spinner(top.get("title") or "")

    return {
        "outputs": outputs or ["eDP-1"],
        "ws_output": ws_output,
        "active": active_ws,
        "entries": entries,
        "focused": focused,
    }


def publish(state: dict, outdir: Path, previous: dict) -> dict:
    """Write one file per (output, workspace). Returns the new rendered map."""
    rendered: dict[str, dict] = {}

    def owner_of(wsid: int) -> str:
        # A rule naming a monitor that is not plugged in is not a claim: those
        # workspaces land on a connected output instead.
        o = state["ws_output"].get(wsid) or ""
        return o if o in state["outputs"] else ""

    for out in state["outputs"]:
        active_here = state["active"].get(out)
        # How full this output is decides the label length for all of its
        # slots, so every slot on one screen stays the same width.
        width = label_width(
            sum(1 for w in state["entries"] if (owner_of(w) or out) == out)
        )
        for wsid in range(1, MAX_WS + 1):
            owner = owner_of(wsid)
            key = f"{out}-{wsid}"
            occupied = wsid in state["entries"]
            # A slot belongs here if a workspace rule assigns it to this
            # output, or if it holds windows, or if you are standing on it.
            # That last case is what covers pressing Ctrl+9 with the external
            # monitor unplugged: Hyprland puts workspace 9 on the laptop, and
            # without this the bar would show no active pill at all.
            mine = (owner == out) if owner else (occupied or active_here == wsid)
            if not mine:
                rendered[key] = {"text": "", "tooltip": "", "class": ["off"]}
                continue
            rendered[key] = render(
                state["entries"].get(wsid), wsid, active_here == wsid, width
            )
        title = state.get("focused", {}).get(out, "")
        rendered[f"{out}-window"] = {
            "text": safe(clip(title, 34, middle=False)) if title else "",
            "tooltip": safe(title),
            "class": ["window"] if title else ["empty"],
        }

    if rendered == previous:
        return previous

    outdir.mkdir(parents=True, exist_ok=True)
    for key, payload in rendered.items():
        if previous.get(key) == payload:
            continue
        tmp = outdir / f".{key}.tmp"
        tmp.write_text(json.dumps(payload, ensure_ascii=False))
        tmp.replace(outdir / f"{key}.json")

    subprocess.run(["pkill", f"-RTMIN+{SIGNAL_NUM}", "waybar"],
                   check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    return rendered


# ── Main loop ───────────────────────────────────────────────────────────────

def run_once() -> int:
    state = collect()
    if state is None:
        print("cannot reach Hyprland", file=sys.stderr)
        return 1
    outdir = Path(runtime_dir()) / "wsctx"
    publish(state, outdir, {})
    # Only echo to a terminal. Under systemd this runs as ExecStartPre and
    # stdout goes to the journal, which is persistent on this machine — that
    # would write browser page titles and repo names to durable disk on every
    # start, for a line nobody reads.
    if sys.stdout.isatty():
        for out in state["outputs"]:
            for wsid in range(1, MAX_WS + 1):
                f = outdir / f"{out}-{wsid}.json"
                if not f.exists():
                    continue
                payload = json.loads(f.read_text())
                if payload.get("text"):
                    print(f"{out}-{wsid}: {payload['text']}")
    return 0


def main() -> int:
    if "--once" in sys.argv:
        return run_once()

    outdir = Path(runtime_dir()) / "wsctx"
    previous: dict = {}
    sel = selectors.DefaultSelector()

    # Wake the select() on a signal rather than relying on a flag, which PEP 475
    # would otherwise retry straight through.
    wake_r, wake_w = os.pipe()
    os.set_blocking(wake_r, False)
    os.set_blocking(wake_w, False)
    signal.set_wakeup_fd(wake_w)
    stopping = False

    def stop(_sig, _frm):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    sel.register(wake_r, selectors.EVENT_READ, "wake")

    conn = None
    pending = False
    deadline = 0.0
    last_full = 0.0

    while not stopping:
        if conn is None:
            p = sock_path(".socket2.sock")
            if p is not None:
                try:
                    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    conn.connect(str(p))
                    conn.setblocking(False)
                    sel.register(conn, selectors.EVENT_READ, "hypr")
                    pending, deadline = True, time.monotonic()
                except OSError:
                    conn = None
            if conn is None:
                time.sleep(1.0)
                if stopping:
                    break
                continue

        now = time.monotonic()
        if pending:
            timeout = max(0.0, deadline - now)
        else:
            timeout = max(0.0, last_full + HEARTBEAT_S - now)

        for key, _mask in sel.select(timeout=timeout):
            if key.data == "wake":
                try:
                    os.read(wake_r, 4096)
                except BlockingIOError:
                    pass
                continue
            try:
                chunk = conn.recv(65536)
            except BlockingIOError:
                continue
            except OSError:
                chunk = b""
            if not chunk:
                # Hyprland went away, or dropped us for being slow. Either way,
                # rebuild the connection from a freshly read signature.
                sel.unregister(conn)
                conn.close()
                conn = None
                os.environ.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
                break
            for line in chunk.decode("utf-8", "replace").splitlines():
                name = line.split(">>", 1)[0]
                if name in WATCHED and not pending:
                    pending = True
                    deadline = time.monotonic() + DEBOUNCE_MS / 1000.0

        if conn is None:
            continue
        if stopping:
            break

        now = time.monotonic()
        if (pending and now >= deadline) or now >= last_full + HEARTBEAT_S:
            state = collect()
            if state is not None:
                previous = publish(state, outdir, previous)
            pending = False
            last_full = now

    if conn is not None:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

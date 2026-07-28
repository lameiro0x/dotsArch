<div align="center">

# 🐧 dotsArch

**Mis dotfiles de Arch Linux — un escritorio Wayland minimalista, oscuro y rápido sobre Hyprland.**

Configuración completa de estética y funcionamiento: compositor, barra, lanzador, terminal, gestor de archivos, prompt y utilidades de TUI.

![Hyprland](https://img.shields.io/badge/WM-Hyprland-1793D1?style=flat-square&logo=hyprland&logoColor=white)
![Wayland](https://img.shields.io/badge/Display-Wayland-FFB13B?style=flat-square)
![Arch Linux](https://img.shields.io/badge/Distro-Arch_Linux-1793D1?style=flat-square&logo=archlinux&logoColor=white)
![Shell](https://img.shields.io/badge/Shell-fish-4AAE46?style=flat-square&logo=gnubash&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

</div>

---

## ✨ Resumen

Un entorno **Wayland** centrado en la simplicidad y la velocidad: tema oscuro coherente,
tipografía *Nerd Font*, blur sutil y un flujo de trabajo por teclado (esquema `hjkl`).
Pensado para un portátil + monitor externo, con workspaces fijos por pantalla.

| Categoría | Programa | Notas |
|---|---|---|
| **Compositor** | [Hyprland](https://hyprland.org) | Tiling dinámico (dwindle), blur, sombras, animaciones |
| **Barra** | [Waybar](https://github.com/Alexays/Waybar) | Módulos propios (audio, brillo, batería, red) en `scripts/` + **workspaces con contexto** (ver abajo) |
| **Lanzador** | [Rofi](https://github.com/davatorium/rofi) | `drun` con tema `style.rasi` propio |
| **Terminal** | [Kitty](https://sw.kovidgoyal.net/kitty/) | + [Alacritty](https://alacritty.org) como alternativa |
| **Gestor de archivos** | [Thunar](https://docs.xfce.org/xfce/thunar/start) | Acciones personalizadas y atajos |
| **TUI de archivos** | [Yazi](https://yazi-rs.github.io) | Navegador de ficheros en terminal |
| **Notificaciones** | [Mako](https://github.com/emersion/mako) | Daemon de notificaciones |
| **Shell** | [fish](https://fishshell.com) | Aliases con `bat`/`lsd`, PATH local |
| **Prompt** | [Starship](https://starship.rs) | Prompt minimalista |
| **Wallpaper** | [Hyprpaper](https://github.com/hyprwm/hyprpaper) / swaybg | |
| **Utilidades** | btop · fastfetch · bat · lsd · micro | Monitor, fetch, `cat`/`ls`/editor bonitos |
| **Tema** | Adwaita Dark · Papirus-Dark · Inter / JetBrainsMono Nerd Font | GTK 3/4 |

## 📦 Estructura

```
dotsArch/
└── .config/
    ├── hypr/        # Hyprland + hyprpaper + scripts
    ├── waybar/      # barra + scripts de módulos
    ├── systemd/     # unidades de usuario (wsctx.service)
    ├── rofi/        # tema del lanzador
    ├── kitty/  alacritty/
    ├── Thunar/  yazi/
    ├── mako/  fish/  starship.toml
    ├── btop/  fastfetch/  bat/  lsd/  micro/
    └── gtk-3.0/  gtk-4.0/
```

## 🚀 Instalación

> ⚠️ Esto sobrescribe tu configuración. Haz copia de seguridad de `~/.config` antes.

### Opción A — con GNU Stow (recomendado)

```bash
git clone https://github.com/lameiro0x/dotsArch.git ~/Repos/dotsArch
cd ~/Repos/dotsArch
stow -t ~ .
```

### Opción B — copia manual

```bash
git clone https://github.com/lameiro0x/dotsArch.git
cp -r dotsArch/.config/* ~/.config/
```

### Después de instalar

El módulo de workspaces necesita su servicio de usuario:

```bash
systemctl --user daemon-reload
systemctl --user enable --now wsctx.service
```

### Dependencias (Arch)

```bash
sudo pacman -S hyprland waybar rofi-wayland kitty alacritty thunar yazi \
               mako fish starship btop fastfetch bat lsd micro \
               hyprpaper swaybg papirus-icon-theme inter-font \
               ttf-jetbrains-mono-nerd grim slurp wl-clipboard \
               noto-fonts-cjk python
```

`noto-fonts-cjk` para el glifo de workspace vacío, `python` para el daemon de la barra
(solo biblioteca estándar).

## ⌨️ Atajos principales (Hyprland)

> Modificador principal: **`Ctrl`** · `Super` para utilidades de ventana.

| Atajo | Acción |
|---|---|
| `Ctrl + Return` | Abrir terminal (kitty) |
| `Ctrl + Space` | Lanzador (rofi) |
| `Ctrl + Q` | Cerrar ventana |
| `Ctrl + h/j/k/l` | Mover el foco |
| `Ctrl + Super + h/j/k/l` | Mover/intercambiar ventana |
| `Ctrl + Shift + h/j/k/l` | Redimensionar |
| `Super + F` | Pantalla completa |
| `Super + V` | Flotante |
| `Ctrl + Tab` | Cambiar foco entre **monitores** |
| `Ctrl + Shift + Tab` | Mover ventana al **otro monitor** |
| `Ctrl + 1..8` | Ir a workspace (portátil) |
| `Ctrl + 9` / `0` / `'` | Ir a workspace 9 / 10 / 11 (monitor externo) |
| `Ctrl + Shift + 1..8` | Mover ventana a workspace (portátil) |
| `Ctrl + Shift + 9` / `0` / `'` | Mover ventana a workspace 9 / 10 / 11 |
| `Print` / `Shift + Print` | Captura pantalla / región |

## 🖥️ Monitores y workspaces

- **Workspaces fijos por pantalla**: portátil (`eDP-1`) → workspaces **1–8**,
  monitor externo (`HDMI-A-1`) → workspaces **9–11**. Cada workspace vive siempre
  en su monitor, así no "saltan" entre pantallas.
- Con el monitor externo desconectado, ir a un workspace suyo (`Ctrl + 9/0/'`) lo
  abre en el portátil y la barra lo muestra igual.
- El monitor externo está configurado a su refresco máximo
  (`monitor=HDMI-A-1,1920x1080@144,auto,1`). Ajusta el nombre/modo a tu hardware
  con `hyprctl monitors`.

## 🪟 Workspaces con contexto

El módulo central de la barra no muestra números: dice **qué hay en cada workspace**.

```
1 󱜙 hito   2 󰊯 GitHub   3 󱜙 lameir…site  ▏4 󱜙 Repos▕  5 󰕷 dotsArch   六   七   八
```

- Un terminal con una sesión de **Claude Code** muestra el repo en el que trabaja.
- Un navegador muestra la página; un editor, el directorio.
- La píldora blanca es el workspace activo. Un **anillo** alrededor de un slot significa
  que esa sesión de Claude Code está **esperando tu respuesta**.
- Los workspaces vacíos se quedan en su numeral CJK, apagados.
- El número de la izquierda es el del workspace: se corresponde con `Ctrl + N`.
- Clic para ir al workspace, rueda para cambiar. Tooltip con el inventario completo.
- La etiqueta se acorta sola según se llena la pantalla (14 caracteres con cuatro
  workspaces ocupados, 8 con ocho), para que la isla no crezca sin límite. Solo cambia
  al ocuparse o vaciarse un workspace: nunca al cambiar de foco ni al retitularse una
  pestaña, así la fila no baila.

Lo alimenta `waybar/scripts/wsctx-daemon.py`, que corre como servicio de usuario y publica
JSON pre-renderizado en `$XDG_RUNTIME_DIR/wsctx/`, despertando a la barra con `SIGRTMIN+9`:

```bash
systemctl --user enable --now wsctx.service
python3 ~/.config/waybar/scripts/wsctx-daemon.py --once   # depurar sin la barra
```

Solo necesita Python 3 de la biblioteca estándar. Sin sesiones de Claude Code funciona
igual: etiqueta terminales, navegadores y editores.

## 📝 Notas

- El widget de música **Aria** (`Ctrl + M`) es un proyecto externo y su `source`
  viene **comentado** en `hypr/hyprland.conf`.
- Aliases de fish: `cat`→`bat`, `ls`/`ll`/`la`→`lsd`.

## 📄 Licencia

[MIT](LICENSE) — úsalo, modifícalo y comparte. Sin garantías.

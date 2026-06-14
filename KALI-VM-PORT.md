# Portar estos dotfiles a una VM Kali (Hyprland)

> Archivo de instrucciones para una sesión de Claude Code que corre **dentro de
> una VM Kali**. Objetivo: instalar Hyprland y dejar este escritorio funcionando
> replicando la config de este repo.

## Entorno destino

- **Kali Linux** (rolling) en **VirtualBox**.
- Gráficos: `VBoxSVGA`, **3D acceleration OFF** → render por **software (llvmpipe)**,
  sin aceleración GPU. Asúmelo en todo.
- **1 solo monitor virtual** (`Virtual-1`), no hay `eDP-1` ni `HDMI-A-1`.

## Cómo obtener la config

```bash
git clone https://github.com/lameiro0x/dotsArch.git ~/dotsArch
```

Las configs están bajo `~/dotsArch/.config/`. Cópialas a `~/.config/` (o symlink).

## Tareas (haz recon en solo-lectura y enséñame el plan ANTES de instalar)

1. **Recon:** versión Kali, `glxinfo | grep "OpenGL renderer"` (esperado
   `llvmpipe`), y `apt-cache policy hyprland` para ver qué versión empaqueta apt.
2. **Instalar Hyprland + ecosistema:** hyprland, waybar, rofi, kitty, alacritty,
   mako, swaybg (o hyprpaper), grim, slurp, wl-clipboard,
   xdg-desktop-portal-hyprland, fish, btop, yazi, starship, fastfetch.
   Fuentes: JetBrainsMono Nerd Font, Noto Sans, Noto Sans CJK, Font Awesome.
3. **Copiar configs** de `~/dotsArch/.config/` a `~/.config/`. Arreglar rutas
   absolutas: cambiar `/home/lameiro0x` por el `$HOME` real de la VM.
4. **CRÍTICO — drift de versión:** la config es de **Hyprland 0.55.3** (Arch). Si
   apt instala otra versión, adapta sintaxis (keywords deprecadas/cambiadas) o no
   arranca.
5. **CRÍTICO — monitores:** reescribe la sección `### MONITORS ###` y los
   `workspace = ... monitor:` de `hyprland.conf`. Hay 2 monitores físicos
   (`eDP-1`, `HDMI-A-1`); la VM tiene 1 (`Virtual-1`). Deja algo como:
   ```
   monitor = Virtual-1, preferred, auto, 1
   # workspaces 1-8 todos en el monitor virtual
   ```
6. **Render software:** si Hyprland no arranca, fuerza:
   ```
   export WLR_RENDERER_ALLOW_SOFTWARE=1
   export LIBGL_ALWAYS_SOFTWARE=1
   ```
   El **blur, sombras y animaciones** pesan mucho sin GPU. Si va a tirones, baja
   `blur passes`, desactiva `shadow` o pon `animations { enabled = false }`.
7. **Wallpapers NO están en el repo** (gitignored). La config apunta a
   `~/Pictures/wallpapers/manos.png` y `minimal-dark.png`. Crea el directorio y
   usa un color sólido o un wallpaper placeholder si no existen; el dueño copiará
   los suyos luego.
8. **Probar:** arranca `Hyprland` desde un TTY e itera hasta que levante.

## Reglas

- Pide confirmación antes de cualquier comando con `sudo`.
- No metas datos sensibles en esta VM; es solo para el ricing.
- Al terminar, recuerda al dueño hacer `/logout` y limpiar `~/.claude` antes de
  clonar/snapshot la VM.

## Referencia rápida (de este repo)

- `.config/hypr/hyprland.conf` — compositor, binds (esquema `hjkl`, mod=SUPER,
  terminal `CTRL+Return`, launcher `CTRL+Space`).
- `.config/waybar/` — barra + scripts propios (audio, brillo, batería, red).
- `.config/rofi/style.rasi` — tema launcher.
- `.config/kitty/`, `.config/alacritty/` — terminales.
- `.config/mako/` — notificaciones.
- Tema: oscuro minimalista, Nerd Font, blur sutil.

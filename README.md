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
| **Barra** | [Waybar](https://github.com/Alexays/Waybar) | Módulos propios (audio, brillo, batería, red) en `scripts/` |
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

### Dependencias (Arch)

```bash
sudo pacman -S hyprland waybar rofi-wayland kitty alacritty thunar yazi \
               mako fish starship btop fastfetch bat lsd micro \
               hyprpaper swaybg papirus-icon-theme inter-font \
               ttf-jetbrains-mono-nerd grim slurp wl-clipboard
```

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
| `Ctrl + 1..8` | Ir a workspace |
| `Ctrl + Shift + 1..8` | Mover ventana a workspace |
| `Print` / `Shift + Print` | Captura pantalla / región |

## 🖥️ Monitores y workspaces

- **Workspaces fijos por pantalla**: portátil (`eDP-1`) → workspaces **1–5**,
  monitor externo (`HDMI-A-1`) → workspaces **6–8**. Cada workspace vive siempre
  en su monitor, así no "saltan" entre pantallas.
- El monitor externo está configurado a su refresco máximo
  (`monitor=HDMI-A-1,1920x1080@144,auto,1`). Ajusta el nombre/modo a tu hardware
  con `hyprctl monitors`.

## 📝 Notas

- El widget de música **Aria** (`Ctrl + M`) es un proyecto externo y su `source`
  viene **comentado** en `hypr/hyprland.conf`.
- Aliases de fish: `cat`→`bat`, `ls`/`ll`/`la`→`lsd`.

## 📄 Licencia

[MIT](LICENSE) — úsalo, modifícalo y comparte. Sin garantías.

#!/usr/bin/env python3
"""Генерирует графику DuoOS: логотипы, обои, фон GRUB, заставку загрузки, картинки установщика.

Запуск (нужны python3-numpy, python3-pil, rsvg-convert, шрифт Inter):
    python3 os/assets/make-assets.py
Результат раскладывается по os/overlay и os/iso; повторный запуск перезаписывает файлы.
"""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

OS = Path(__file__).resolve().parent.parent
ASSETS = OS / "assets"
OVERLAY = OS / "overlay"

# Палитра DuoOS: глубокий индиго -> фиолетовый -> бирюзовый
BG = (9, 12, 28)
BLOBS = [  # (x, y, радиус, цвет) в долях экрана
    (0.18, 0.78, 0.55, (91, 76, 255)),
    (0.72, 0.30, 0.50, (34, 211, 238)),
    (0.95, 0.95, 0.45, (236, 72, 153)),
    (0.45, 0.10, 0.40, (139, 92, 246)),
    (0.05, 0.10, 0.35, (37, 99, 235)),
]

LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#6d5dfc"/>
      <stop offset="0.55" stop-color="#8b5cf6"/>
      <stop offset="1" stop-color="#22d3ee"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.28"/>
      <stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="240" height="240" rx="56" fill="url(#bg)"/>
  <rect x="8" y="8" width="240" height="240" rx="56" fill="url(#shine)"/>
  <circle cx="100" cy="128" r="58" fill="none" stroke="#ffffff" stroke-width="20"/>
  <circle cx="156" cy="128" r="58" fill="none" stroke="#ffffff" stroke-opacity="0.72" stroke-width="20"/>
</svg>
"""

# Монохромный значок для верхней панели (аналог «яблока» в строке меню)
LOGO_SYMBOLIC_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
  <style type="text/css" id="current-color-scheme">.ColorScheme-Text { color:#fcfcfc; }</style>
  <g class="ColorScheme-Text" fill="none" stroke="currentColor" stroke-width="1.6">
    <circle cx="6" cy="8" r="4.2"/>
    <circle cx="10" cy="8" r="4.2" stroke-opacity="0.7"/>
  </g>
</svg>
"""

# Значок «Установить DuoOS» для рабочего стола live-сессии
INSTALL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#6d5dfc"/><stop offset="1" stop-color="#22d3ee"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="240" height="240" rx="56" fill="url(#bg)"/>
  <path d="M128 52v104M84 116l44 44 44-44" fill="none" stroke="#fff" stroke-width="22"
        stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="64" y="182" width="128" height="22" rx="11" fill="#fff"/>
</svg>
"""


def wallpaper(w: int, h: int, darken: float = 1.0) -> Image.Image:
    """Мягкий «жидкий» градиент в духе обоев macOS."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xx /= w
    yy /= h
    aspect = w / h
    img = np.zeros((h, w, 3), np.float32) + np.array(BG, np.float32)
    for bx, by, r, col in BLOBS:
        d2 = ((xx - bx) * aspect) ** 2 + (yy - by) ** 2
        a = np.exp(-d2 / (2 * (r * 0.55) ** 2))[..., None] * 0.85
        img = img * (1 - a) + np.array(col, np.float32) * a
    # Лёгкие диагональные волны — объём без рисунка
    waves = 0.5 + 0.5 * np.sin((xx * 3.1 + yy * 1.7) * np.pi + np.sin(yy * 4.0) * 0.8)
    img *= (0.82 + 0.18 * waves)[..., None]
    # Виньетка
    v = 1 - 0.35 * (((xx - 0.5) * 1.6) ** 2 + ((yy - 0.5) * 1.6) ** 2)
    img *= np.clip(v, 0.55, 1)[..., None] * darken
    # Шум против полос градиента
    img += np.random.default_rng(7).normal(0, 1.2, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))


def svg_to_png(svg: str, out: Path, size: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(out)],
                   input=svg.encode(), check=True)


def text_png(svg: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsvg-convert", "-o", str(out)], input=svg.encode(), check=True)


def main() -> None:
    icons = OVERLAY / "usr/share/icons/hicolor"
    (icons / "scalable/apps").mkdir(parents=True, exist_ok=True)
    (icons / "scalable/apps/duoos-logo.svg").write_text(LOGO_SVG)
    (icons / "scalable/apps/duoos-logo-symbolic.svg").write_text(LOGO_SYMBOLIC_SVG)
    (icons / "scalable/apps/duoos-install.svg").write_text(INSTALL_SVG)
    for s in (16, 22, 24, 32, 48, 64, 128, 256):
        svg_to_png(LOGO_SVG, icons / f"{s}x{s}/apps/duoos-logo.png", s)
        svg_to_png(INSTALL_SVG, icons / f"{s}x{s}/apps/duoos-install.png", s)

    share = OVERLAY / "usr/share/duoos"
    svg_to_png(LOGO_SVG, share / "logo.png", 256)

    # Обои (пакет Plasma) + превью
    wp = OVERLAY / "usr/share/wallpapers/DuoOS/contents/images"
    wp.mkdir(parents=True, exist_ok=True)
    big = wallpaper(3840, 2160)
    big.save(wp / "3840x2160.jpg", quality=92)
    big.resize((1920, 1080), Image.LANCZOS).save(wp / "1920x1080.jpg", quality=92)
    big.resize((400, 225), Image.LANCZOS).save(wp.parent / "screenshot.jpg", quality=90)

    # Фон GRUB: затемнённые обои + логотип и название
    grub = wallpaper(1920, 1080, darken=0.55)
    logo = Path("/tmp/duoos-logo-160.png")
    svg_to_png(LOGO_SVG, logo, 160)
    grub.paste(Image.open(logo), (880, 250), Image.open(logo))
    title = Path("/tmp/duoos-title.png")
    text_png("""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="90">
      <text x="300" y="66" text-anchor="middle" font-family="Inter" font-weight="600"
            font-size="64" fill="#ffffff">DuoOS</text></svg>""", title)
    t = Image.open(title)
    grub.paste(t, (660, 420), t)
    (OS / "iso/theme").mkdir(parents=True, exist_ok=True)
    grub.save(OS / "iso/theme/background.png", optimize=True)

    # Загрузочная заставка (Plymouth): логотип по центру + подпись внизу
    svg_to_png(LOGO_SVG, share / "plymouth-logo.png", 160)
    text_png("""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="56">
      <text x="100" y="42" text-anchor="middle" font-family="Inter" font-weight="600"
            font-size="36" fill="#ffffff">DuoOS</text></svg>""", share / "plymouth-watermark.png")

    # Установщик Calamares
    cal = OVERLAY / "etc/calamares/branding/duoos"
    cal.mkdir(parents=True, exist_ok=True)
    svg_to_png(LOGO_SVG, cal / "logo.png", 128)
    svg_to_png(LOGO_SVG, cal / "icon.png", 64)
    welcome = wallpaper(960, 360, darken=0.8)
    l2 = Path("/tmp/duoos-logo-120.png")
    svg_to_png(LOGO_SVG, l2, 120)
    welcome.paste(Image.open(l2), (140, 120), Image.open(l2))
    text_png("""<svg xmlns="http://www.w3.org/2000/svg" width="620" height="200">
      <text x="0" y="80" font-family="Inter" font-weight="700" font-size="72" fill="#fff">DuoOS</text>
      <text x="4" y="130" font-family="Inter" font-size="28" fill="#e0e7ff">Операционная система для разработчиков</text>
      </svg>""", Path("/tmp/duoos-welcome-text.png"))
    wt = Image.open("/tmp/duoos-welcome-text.png")
    welcome.paste(wt, (300, 105), wt)
    welcome.save(cal / "welcome.png", optimize=True)
    wallpaper(1280, 720, darken=0.7).save(cal / "slide-bg.jpg", quality=88)

    # Фото пользователя по умолчанию
    svg_to_png(LOGO_SVG, OVERLAY / "etc/skel/.face", 192)
    print("Графика DuoOS сгенерирована")


if __name__ == "__main__":
    main()

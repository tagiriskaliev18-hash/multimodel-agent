#!/usr/bin/env python3
"""Тема оформления окон DuoOS для KWin (Aurorae): тёмный заголовок, скруглённые углы,
мягкая тень и кнопки-«светофор» слева, как в macOS.

Рамка рисуется растром (Pillow) и нарезается на 9 частей FrameSvg, кнопки — вектором.
"""
import base64
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "overlay/usr/share/aurorae/themes/DuoOS"

PAD_SIDE, PAD_TOP, PAD_BOTTOM = 16, 10, 20  # поля под тень
RADIUS = 10
TITLE_H = 32
CENTER = 40  # размер растягиваемой середины

STATES = {
    # префикс: (цвет заголовка, цвет контура, непрозрачность тени)
    "decoration": ((42, 43, 52), (255, 255, 255, 26), 150),
    "decoration-inactive": ((33, 34, 41), (255, 255, 255, 14), 90),
}


def frame(title_rgb, outline, shadow_alpha) -> Image.Image:
    left = PAD_SIDE + RADIUS
    top = PAD_TOP + TITLE_H
    bottom = PAD_BOTTOM + RADIUS
    w = left * 2 + CENTER
    h = top + CENTER + bottom
    win = (PAD_SIDE, PAD_TOP, w - PAD_SIDE - 1, h - PAD_BOTTOM - 1)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (win[0], win[1] + 4, win[2], win[3] + 4), RADIUS, fill=(0, 0, 0, shadow_alpha))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(7)))

    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle(win, RADIUS, fill=title_rgb + (255,), outline=outline, width=1)
    # Тонкий блик по верхней кромке заголовка
    d.line((win[0] + RADIUS, win[1] + 1, win[2] - RADIUS, win[1] + 1), fill=(255, 255, 255, 22))
    return Image.alpha_composite(img, body)


def png_b64(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def decoration_svg() -> str:
    left = PAD_SIDE + RADIUS
    top = PAD_TOP + TITLE_H
    bottom = PAD_BOTTOM + RADIUS
    cols = [(0, left), (left, CENTER), (left + CENTER, left)]
    rows = [(0, top), (top, CENTER), (top + CENTER, bottom)]
    names = [["topleft", "top", "topright"], ["left", "center", "right"],
             ["bottomleft", "bottom", "bottomright"]]
    parts = []
    offset_y = 0
    for prefix, (rgb, outline, sa) in STATES.items():
        im = frame(rgb, outline, sa)
        for r, (y, hh) in enumerate(rows):
            for c, (x, ww) in enumerate(cols):
                piece = im.crop((x, y, x + ww, y + hh))
                parts.append(
                    f'<image id="{prefix}-{names[r][c]}" x="{x}" y="{y + offset_y}" '
                    f'width="{ww}" height="{hh}" preserveAspectRatio="none" '
                    f'xlink:href="data:image/png;base64,{png_b64(piece)}"/>')
        offset_y += im.height + 20
    width = 2 * (PAD_SIDE + RADIUS) + CENTER
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{offset_y}">\n' + "\n".join(parts) + "\n</svg>\n")


BUTTONS = {
    # файл: (цвет, значок при наведении)
    "close": ("#ff5f57", '<path d="M4.6 4.6l4.8 4.8M9.4 4.6l-4.8 4.8"/>'),
    "minimize": ("#febc2e", '<path d="M4 7h6"/>'),
    "maximize": ("#28c840", '<path d="M4.3 7h5.4M7 4.3v5.4"/>'),
    "restore": ("#28c840", '<path d="M4.3 7h5.4"/>'),
}


def button_svg(color: str, glyph: str) -> str:
    size = 14
    states = [
        ("active", color, False, 1.0),
        ("hover", color, True, 1.0),
        ("pressed", color, True, 0.75),
        ("inactive", "#4b4c57", False, 1.0),
        ("hover-inactive", color, True, 1.0),
        ("pressed-inactive", color, True, 0.75),
        ("deactivated", "#3a3b44", False, 1.0),
        ("deactivated-inactive", "#3a3b44", False, 1.0),
    ]
    out = []
    for i, (name, col, show_glyph, op) in enumerate(states):
        x = i * (size + 4)
        g = (f'<g transform="translate({x} 0)" stroke="#4d0000" stroke-opacity="0.65" '
             f'stroke-width="1.4" stroke-linecap="round" fill="none">{glyph}</g>') if show_glyph else ""
        out.append(
            f'<g id="{name}-center">'
            f'<rect x="{x}" y="0" width="{size}" height="{size}" fill="#000" fill-opacity="0.001"/>'
            f'<circle cx="{x + 7}" cy="7" r="6.2" fill="{col}" fill-opacity="{op}" '
            f'stroke="#000" stroke-opacity="0.18" stroke-width="0.6"/>{g}</g>')
    width = len(states) * (size + 4)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{size}">\n'
            + "\n".join(out) + "\n</svg>\n")


RC = f"""[General]
ActiveTextColor=#e6e7ee
InactiveTextColor=#80828f
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=120
Shadow=true

[Layout]
BorderLeft=0
BorderRight=0
BorderBottom=0
TitleEdgeTop=0
TitleEdgeBottom=0
TitleEdgeLeft=12
TitleEdgeRight=12
TitleEdgeTopMaximized=0
TitleEdgeBottomMaximized=0
TitleEdgeLeftMaximized=12
TitleEdgeRightMaximized=12
TitleBorderLeft=8
TitleBorderRight=8
TitleHeight={TITLE_H}
TitleHeightMaximized={TITLE_H}
ButtonWidth=14
ButtonHeight=14
ButtonSpacing=8
ButtonMarginTop={(TITLE_H - 14) // 2}
ButtonMarginTopMaximized={(TITLE_H - 14) // 2}
ExplicitButtonSpacer=10
PaddingTop={PAD_TOP}
PaddingBottom={PAD_BOTTOM}
PaddingLeft={PAD_SIDE}
PaddingRight={PAD_SIDE}
"""

METADATA_DESKTOP = """[Desktop Entry]
Name=DuoOS
Comment=Тёмная тема окон с кнопками-«светофором»
X-KDE-PluginInfo-Author=DuoOS
X-KDE-PluginInfo-Name=DuoOS
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-License=GPL-2.0-or-later
X-KDE-PluginInfo-EnabledByDefault=true
"""

METADATA_JSON = """{
    "KPlugin": {
        "Authors": [ { "Name": "DuoOS" } ],
        "Description": "Тёмная тема окон с кнопками-«светофором»",
        "Id": "DuoOS",
        "License": "GPL-2.0-or-later",
        "Name": "DuoOS",
        "Version": "1.0"
    }
}
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "decoration.svg").write_text(decoration_svg())
    for name, (color, glyph) in BUTTONS.items():
        (OUT / f"{name}.svg").write_text(button_svg(color, glyph))
    (OUT / "DuoOSrc").write_text(RC)
    (OUT / "metadata.desktop").write_text(METADATA_DESKTOP)
    (OUT / "metadata.json").write_text(METADATA_JSON)
    print("Тема окон DuoOS сгенерирована:", OUT)


if __name__ == "__main__":
    main()

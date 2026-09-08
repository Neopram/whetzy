"""
Generate all iOS and Android icon PNGs from the Whetzy brand design.

Usage:
    python scripts/generate_icons.py

Outputs:
    docs/store/icons/ios/          — AppIcon.appiconset ready to drag into Xcode
    docs/store/icons/android/      — mipmap-* directories + Play Store 512px
    frontend/android/app/src/main/res/mipmap-*/ic_launcher*.png  — replaces Capacitor defaults
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

# ── Brand colours ──────────────────────────────────────────────────────────────
BG_TOP    = (28, 176, 246)   # #1CB0F6
BG_BOTTOM = (11, 114, 176)   # #0B72B0
FG        = (255, 255, 255)  # white W

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(SCRIPT_DIR)

# OneDrive blocks Python from creating new files in synced dirs (known gotcha).
# Write to scratchpad, then PowerShell copies them to the repo.
import tempfile
_SCRATCH = os.environ.get(
    "ICON_SCRATCH",
    os.path.join(tempfile.gettempdir(), "whetzy_icons"),
)
OUT_IOS    = os.path.join(_SCRATCH, "ios", "AppIcon.appiconset")
OUT_AND    = os.path.join(_SCRATCH, "android")
ANDROID_RES_SCRATCH = os.path.join(_SCRATCH, "android_res")

# ── Size lists ─────────────────────────────────────────────────────────────────
IOS_SIZES = [
    (1024, "ios-marketing"),
    (180,  "iphone-60@3x"),
    (120,  "iphone-60@2x"),
    (167,  "ipad-83.5@2x"),
    (152,  "ipad-76@2x"),
    (87,   "iphone-29@3x"),
    (80,   "spotlight-40@2x"),
    (76,   "ipad-76@1x"),
    (60,   "iphone-60@1x"),
    (58,   "iphone-29@2x"),
    (40,   "spotlight-40@1x"),
    (29,   "iphone-29@1x"),
    (20,   "notification-20@1x"),
]

ANDROID_DENSITIES = [
    ("mipmap-xxxhdpi", 192),
    ("mipmap-xxhdpi",  144),
    ("mipmap-xhdpi",    96),
    ("mipmap-hdpi",     72),
    ("mipmap-mdpi",     48),
    ("mipmap-ldpi",     36),
]

PLAY_STORE_SIZE = 512


def make_dirs(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def gradient_background(size: int) -> Image.Image:
    """Create a vertical gradient background with rounded corners."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for y in range(size):
        t = y / (size - 1)
        r = round(BG_TOP[0] + t * (BG_BOTTOM[0] - BG_TOP[0]))
        g = round(BG_TOP[1] + t * (BG_BOTTOM[1] - BG_TOP[1]))
        b = round(BG_TOP[2] + t * (BG_BOTTOM[2] - BG_TOP[2]))
        draw.line([(0, y), (size - 1, y)], fill=(r, g, b, 255))

    # Rounded corner mask (radius ≈ 22 % of size, matching iOS guideline)
    radius = max(1, round(size * 0.22))
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def draw_w(img: Image.Image, size: int) -> None:
    """Draw a bold white W centred on `img` (in-place)."""
    draw = ImageDraw.Draw(img)

    # W points defined on a 1024 grid, then scaled
    s = size / 1024.0
    raw = [
        (192, 260),
        (312, 700),
        (432, 420),
        (552, 700),
        (672, 420),
        (792, 700),
        (832, 260),
    ]
    pts = [(x * s, y * s) for x, y in raw]
    stroke = max(2, round(108 * s))

    # draw with round caps by drawing segments between consecutive points
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        # draw with extra width for round join effect
        draw.line([(x0, y0), (x1, y1)], fill=FG, width=stroke, joint="curve")

    # round caps at endpoints
    cap_r = stroke // 2
    for x, y in (pts[0], pts[-1]):
        draw.ellipse([x - cap_r, y - cap_r, x + cap_r, y + cap_r], fill=FG)


def render_icon(size: int, composite_bg: bool = True) -> Image.Image:
    """Render a single icon at `size` × `size`."""
    base = gradient_background(size)
    draw_w(base, size)
    if composite_bg:
        result = Image.new("RGBA", (size, size), (255, 255, 255, 255))
        result.paste(base, mask=base.split()[3])
        return result.convert("RGB")
    return base


def save(img: Image.Image, path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    img.save(path, "PNG", optimize=True)
    kb = os.path.getsize(path) // 1024
    print(f"  ✓ {os.path.relpath(path, ROOT)}  ({img.size[0]}px, {kb} KB)")


def generate_ios() -> None:
    print("\n── iOS ───────────────────────────────────────────")
    contents_icons = []
    for size, name in IOS_SIZES:
        img = render_icon(size)
        fname = f"Icon-{size}.png"
        save(img, os.path.join(OUT_IOS, fname))
        contents_icons.append(f'    {{"filename": "{fname}", "idiom": "universal", "scale": "1x", "size": "{size}x{size}"}}')

    # Contents.json
    contents = (
        '{\n  "images": [\n'
        + ",\n".join(contents_icons)
        + '\n  ],\n  "info": {"author": "whetzy-generate-icons", "version": 1}\n}\n'
    )
    with open(os.path.join(OUT_IOS, "Contents.json"), "w") as f:
        f.write(contents)
    print(f"  ✓ Contents.json written")


def generate_android() -> None:
    print("\n── Android ───────────────────────────────────────")
    # Play Store
    img = render_icon(PLAY_STORE_SIZE)
    save(img, os.path.join(OUT_AND, "play-store-512.png"))

    # mipmap directories — docs/store/icons/android/
    for density, size in ANDROID_DENSITIES:
        img = render_icon(size)
        for fname in ("ic_launcher.png", "ic_launcher_round.png"):
            save(img, os.path.join(OUT_AND, density, fname))

    # Write android_res versions to scratch too (for copy step)
    print("\n── Android res (scratch) ─────────────────────────")
    for density, size in ANDROID_DENSITIES:
        img = render_icon(size)
        for fname in ("ic_launcher.png", "ic_launcher_round.png"):
            save(img, os.path.join(ANDROID_RES_SCRATCH, density, fname))
        img_fg = gradient_background(size).convert("RGBA")
        draw_w(img_fg, size)
        save(img_fg.convert("RGBA"), os.path.join(ANDROID_RES_SCRATCH, density, "ic_launcher_foreground.png"))


def generate_splash_placeholder() -> None:
    """Create a minimal 2048×2048 splash screen (white bg + centred W)."""
    print("\n── Splash ────────────────────────────────────────")
    size = 2048
    img = Image.new("RGB", (size, size), (247, 247, 247))  # --le-bg #F7F7F7

    # Draw just the W, centred in the safe zone (half of 2048)
    icon_size = 512
    icon = render_icon(icon_size)
    x = (size - icon_size) // 2
    y = (size - icon_size) // 2
    img.paste(icon, (x, y))

    path = os.path.join(_SCRATCH, "splash-2048.png")
    save(img, path)


if __name__ == "__main__":
    make_dirs(OUT_IOS, OUT_AND, ANDROID_RES_SCRATCH)
    generate_ios()
    generate_android()
    generate_splash_placeholder()
    print(f"\nAll icons written to scratch: {_SCRATCH}")
    print("Run copy step to move to repo (see PowerShell command at bottom of this script).")
    print("\nPowerShell copy commands:")
    print(f'  Copy-Item -Recurse -Force "{OUT_IOS}" "C:\\Users\\feder\\Desktop\\Banco de preguntas\\python\\learning-engine\\docs\\store\\icons\\ios"')
    print(f'  Copy-Item -Recurse -Force "{OUT_AND}\\*" "C:\\Users\\feder\\Desktop\\Banco de preguntas\\python\\learning-engine\\docs\\store\\icons\\android"')
    print(f'  # Android res:')
    for density, _ in ANDROID_DENSITIES:
        src = os.path.join(ANDROID_RES_SCRATCH, density)
        dst = f"C:\\Users\\feder\\Desktop\\Banco de preguntas\\python\\learning-engine\\frontend\\android\\app\\src\\main\\res\\{density}"
        print(f'  Copy-Item -Force "{src}\\*.png" "{dst}"')

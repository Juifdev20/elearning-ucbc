"""
Génère les icônes PWA / favicon / écran de chargement à la charte de
l'application (dégradé bleu de marque + glyphe "école"), pour remplacer
le branding par défaut de Flet dans assets/ (favicon, icônes, manifest).

À relancer si la charte graphique change. Usage : python scripts/generate_brand_icons.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "assets" / "icons"
ASSETS_DIR = ROOT / "assets"
FONT_PATH = ROOT / "venv" / "Lib" / "site-packages" / "flet_web" / "web" / "assets" / "fonts" / "MaterialIcons-Regular.otf"
SCHOOL_GLYPH = chr(0xF012E)  # "school_rounded" — même glyphe que ft.Icons.SCHOOL_ROUNDED dans l'app

BLUE_DARK = (30, 58, 138)     # #1E3A8A
BLUE = (37, 99, 235)          # #2563EB

MASTER_SIZE = 512


def _gradient_square(size: int) -> Image.Image:
    """Carré plein dégradé diagonal (haut-gauche -> bas-droite), sans coins arrondis."""
    pixels = []
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            r = round(BLUE_DARK[0] + (BLUE[0] - BLUE_DARK[0]) * t)
            g = round(BLUE_DARK[1] + (BLUE[1] - BLUE_DARK[1]) * t)
            b = round(BLUE_DARK[2] + (BLUE[2] - BLUE_DARK[2]) * t)
            pixels.append((r, g, b, 255))
    img = Image.new("RGBA", (size, size))
    img.putdata(pixels)
    return img


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def _with_glyph(base: Image.Image, glyph_ratio: float) -> Image.Image:
    """Colle le glyphe blanc "école" centré sur `base` (carré RGBA)."""
    size = base.size[0]
    out = base.copy()
    font = ImageFont.truetype(str(FONT_PATH), int(size * glyph_ratio))
    glyph_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(glyph_layer)
    bbox = d.textbbox((0, 0), SCHOOL_GLYPH, font=font)
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = (size / 2 - gw / 2 - bbox[0], size / 2 - gh / 2 - bbox[1])
    d.text(pos, SCHOOL_GLYPH, font=font, fill=(255, 255, 255, 255))
    out.alpha_composite(glyph_layer)
    return out


def make_regular_icon(size: int, corner_ratio: float = 0.22) -> Image.Image:
    """Icône standard : coins arrondis, glyphe bien visible."""
    base = _gradient_square(MASTER_SIZE).resize((size, size), Image.LANCZOS)
    mask = _rounded_mask(size, int(size * corner_ratio))
    rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rounded.paste(base, (0, 0), mask)
    return _with_glyph(rounded, glyph_ratio=0.52)


def make_maskable_icon(size: int) -> Image.Image:
    """Icône 'maskable' PWA : fond plein bord-à-bord, glyphe dans la zone
    de sécurité (~80% du diamètre central) pour survivre au masquage OS."""
    base = _gradient_square(MASTER_SIZE).resize((size, size), Image.LANCZOS)
    return _with_glyph(base, glyph_ratio=0.36)


def make_apple_touch_icon(size: int) -> Image.Image:
    """iOS applique lui-même l'arrondi : image carrée pleine, sans coin arrondi."""
    base = _gradient_square(MASTER_SIZE).resize((size, size), Image.LANCZOS)
    return _with_glyph(base, glyph_ratio=0.52)


def make_loading_animation(size: int = 300) -> Image.Image:
    """Logo affiché (avec fond transparent) pendant le chargement initial."""
    base = _gradient_square(MASTER_SIZE).resize((size, size), Image.LANCZOS)
    mask = _rounded_mask(size, int(size * 0.30))
    rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rounded.paste(base, (0, 0), mask)
    return _with_glyph(rounded, glyph_ratio=0.5)


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    make_regular_icon(192).save(ICONS_DIR / "icon-192.png")
    make_regular_icon(512).save(ICONS_DIR / "icon-512.png")
    make_maskable_icon(192).save(ICONS_DIR / "icon-maskable-192.png")
    make_maskable_icon(512).save(ICONS_DIR / "icon-maskable-512.png")
    make_apple_touch_icon(192).save(ICONS_DIR / "apple-touch-icon-192.png")
    make_loading_animation(300).save(ICONS_DIR / "loading-animation.png")

    # Favicon : petit carré net (32px suffit pour un onglet de navigateur).
    make_regular_icon(64, corner_ratio=0.18).save(ASSETS_DIR / "favicon.png")

    print("Icônes de marque générées dans", ICONS_DIR, "et", ASSETS_DIR / "favicon.png")


if __name__ == "__main__":
    main()

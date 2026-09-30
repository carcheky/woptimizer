"""Sistema de diseno y tokens visuales para woptimizer.

Este modulo define UNICAMENTE tokens de diseno (colores semanticos,
escala tipografica y radios de borde) y funciones de calculo de contraste WCAG AA.
No contiene widgets, no instancia CustomTkinter ni accede a logica de negocio.
"""

from typing import Final, Tuple

# --- Colores Semanticos ---
SURFACE: Final[str] = "#121212"
SURFACE_ALT: Final[str] = "#1a1a1a"
SURFACE_SUNKEN: Final[str] = "#151515"
SURFACE_HOVER: Final[str] = "#262626"
BORDER: Final[str] = "#2e2e2e"

TEXT_PRIMARY: Final[str] = "#ffffff"
TEXT_MUTED: Final[str] = "#888888"

# Marca y Estados
# Opcion A (adoptada): Gaming = Verde #1DB954. El rojo queda exclusivo para peligro.
GAMING: Final[str] = "#1DB954"
GAMING_HOVER: Final[str] = "#1aa34a"

ACCENT: Final[str] = "#3B8ED0"
ACCENT_HOVER: Final[str] = "#1f6aa5"

DANGER: Final[str] = "#c22d2d"
DANGER_HOVER: Final[str] = "#a82424"

WARNING: Final[str] = "#f59e0b"
SUCCESS: Final[str] = "#22c55e"

# --- Escala Tipografica (Exactamente 6 tamanos) ---
FONT_SIZE_TINY: Final[int] = 9
FONT_SIZE_SMALL: Final[int] = 11
FONT_SIZE_BODY: Final[int] = 13
FONT_SIZE_SUBHEADER: Final[int] = 14
FONT_SIZE_HEADER: Final[int] = 18
FONT_SIZE_HERO: Final[int] = 24

FONT_SIZES: Final[Tuple[int, ...]] = (9, 11, 13, 14, 18, 24)

# --- Radios de Borde (Exactamente 3 tamanos) ---
RADIUS_SMALL: Final[int] = 4
RADIUS_MEDIUM: Final[int] = 6
RADIUS_LARGE: Final[int] = 8

RADII: Final[Tuple[int, ...]] = (4, 6, 8)


# --- Utilidades WCAG AA ---
def _srgb_channel_to_linear(c: float) -> float:
    """Convierte un canal sRGB normalizado [0, 1] a luminancia lineal segun WCAG 2.1."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """Calcula la luminancia relativa WCAG 2.1 de un color hexadecimal #RRGGBB."""
    hex_clean = hex_color.lstrip("#")
    if len(hex_clean) != 6:
        raise ValueError(f"Color invalido para WCAG: {hex_color}")
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0
    r_lin = _srgb_channel_to_linear(r)
    g_lin = _srgb_channel_to_linear(g)
    b_lin = _srgb_channel_to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calcula el ratio de contraste (L1 + 0.05) / (L2 + 0.05) entre dos colores segun WCAG 2.1."""
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_wcag_aa(fg: str, bg: str, large_text: bool = False) -> bool:
    """Comprueba si el contraste cumple WCAG AA (4.5:1 para texto normal, 3.0:1 para texto grande)."""
    threshold = 3.0 if large_text else 4.5
    return contrast_ratio(fg, bg) >= threshold

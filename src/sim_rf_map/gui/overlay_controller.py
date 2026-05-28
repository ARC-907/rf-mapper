"""Overlay rendering logic and toggle handlers."""

from PIL import Image


def composite_images(base: Image.Image, overlay: Image.Image) -> Image.Image:
    """Return overlay composited on base image."""
    base = base.convert("RGBA")
    overlay = overlay.convert("RGBA")
    return Image.alpha_composite(base, overlay)

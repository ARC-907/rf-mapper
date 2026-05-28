import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


def overlay_with_legend(
    base: Image.Image, data: np.ndarray, label: str = "Signal Loss (dB)", cmap: str = "magma"
) -> Image.Image:
    """Return ``base`` with a colorbar legend pasted in the corner."""
    fig, ax = plt.subplots(figsize=(1, 4))
    norm = plt.Normalize(vmin=float(data.min()), vmax=float(data.max()))
    fig.subplots_adjust(left=0.5, right=0.8)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax, label=label)
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = fig.canvas.renderer.buffer_rgba()
    image = np.frombuffer(buf, dtype=np.uint8).reshape((h, w, 4))[:, :, :3]
    legend_img = Image.fromarray(image).rotate(270, expand=True)
    plt.close(fig)

    combined = base.convert("RGBA")
    combined.paste(legend_img, (10, 10), legend_img.convert("RGBA"))
    return combined

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 - imported for 3D projection


def plot_voxel_volume(voxels: np.ndarray, color: str = "gray", alpha: float = 0.3) -> None:
    """Render the 3D voxel terrain using matplotlib."""
    Z, Y, X = voxels.shape
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.voxels(voxels, facecolors=color, edgecolors="k", alpha=alpha)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Voxel Terrain Structure")
    plt.tight_layout()
    plt.show()

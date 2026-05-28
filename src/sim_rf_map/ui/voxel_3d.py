"""Minimal 3D voxel viewer using pyqtgraph."""

from pyqtgraph.Qt import QtWidgets
import pyqtgraph.opengl as gl
import numpy as np


class Voxel3DViewer(QtWidgets.QWidget):
    """Display a voxel volume in a simple isometric window."""

    def __init__(self, volume: np.ndarray):
        super().__init__()
        self.setWindowTitle("3D Voxel Terrain View")
        self.view = gl.GLViewWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.plot_voxel_volume(volume)

    def plot_voxel_volume(self, volume: np.ndarray) -> None:
        """Render ``volume`` using a scatter plot of occupied cells."""
        pos = np.argwhere(volume > 0)
        color = np.ones((pos.shape[0], 4), dtype=np.float32)
        color[:, :3] = [0.2, 0.8, 0.2]
        scatter = gl.GLScatterPlotItem(pos=pos, size=1.0, color=color)
        self.view.addItem(scatter)

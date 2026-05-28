"""3D mesh utilities for rendering transmitter signal cones."""

from __future__ import annotations

from pyqtgraph.opengl import GLMeshItem, MeshData
import numpy as np


def create_cone(center: tuple[float, float, float], direction, height: float = 15, radius: float = 10) -> GLMeshItem:
    """Return a semi-transparent cone mesh positioned at ``center``."""
    n_faces = 32
    angles = np.linspace(0, 2 * np.pi, n_faces)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    z = np.zeros_like(x)

    tip = np.array([[0, 0, height]])
    base = np.stack([x, y, z], axis=1)

    vertices = np.concatenate([tip, base], axis=0)
    faces = [[0, i + 1, (i + 2 if i + 1 < n_faces else 1)] for i in range(n_faces)]
    mesh = MeshData(vertexes=vertices, faces=np.array(faces))
    cone = GLMeshItem(meshdata=mesh, color=(1, 0, 0, 0.3), drawEdges=False)
    cone.translate(*center)
    return cone

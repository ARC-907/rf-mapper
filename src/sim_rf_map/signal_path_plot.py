import matplotlib.pyplot as plt


def plot_signal_profile(
    path: list[tuple[int, int, float]], tx_height: float = 1.65, dem_color: str = "brown"
) -> None:
    """Plot elevation profile along a traced RF path."""
    distances = list(range(len(path)))
    elevations = [h for (_, _, h) in path]
    signal_line = [e + tx_height * (1 - i / len(path)) for i, e in enumerate(elevations)]
    plt.figure(figsize=(10, 5))
    plt.plot(distances, elevations, label="Terrain", color=dem_color)
    plt.plot(distances, signal_line, label="Signal Path", linestyle="--", color="blue")
    plt.title("RF Path Elevation Profile")
    plt.xlabel("Path Index")
    plt.ylabel("Elevation (m)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

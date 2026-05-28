# OnyxGeoImage API Documentation

This document provides comprehensive documentation for the OnyxGeoImage API, including classes, methods, and functions.

## Table of Contents

1. [Core Components](#core-components)
2. [GUI Components](#gui-components)
3. [CLI Components](#cli-components)
4. [Physics Models](#physics-models)
5. [Utilities](#utilities)

## Core Components

### RFAnalyzerApp

The main application class that provides the GUI interface for the RF propagation simulator.

```python
class RFAnalyzerApp:
    def __init__(self, root: tk.Tk):
        """
        Initialize the RF Analyzer application.
        
        Args:
            root: The tkinter root window
        """
        # ...
```

#### Key Methods

- `open_image()`: Opens an image file for analysis
- `analyze()`: Performs RF propagation analysis on the loaded image
- `show_voxels()`: Displays 3D voxel visualization of the RF propagation
- `export_overlay()`: Exports the RF overlay as an image
- `refresh()`: Refreshes the display
- `reset_all()`: Resets the application state

### Propagator

The propagator class that performs RF propagation calculations.

```python
class Propagator:
    def __init__(self, dem: np.ndarray, settings: dict):
        """
        Initialize the propagator.
        
        Args:
            dem: Digital Elevation Model as a numpy array
            settings: Dictionary of propagation settings
        """
        # ...
    
    def compute_coverage(self, tx_points: list) -> np.ndarray:
        """
        Compute RF coverage for the given transmitter points.
        
        Args:
            tx_points: List of transmitter points as (x, y) tuples
            
        Returns:
            Coverage map as a numpy array
        """
        # ...
```

### Voxelizer

The voxelizer class that creates 3D voxel representations of RF propagation.

```python
class Voxelizer:
    def __init__(self, dem: np.ndarray, settings: dict):
        """
        Initialize the voxelizer.
        
        Args:
            dem: Digital Elevation Model as a numpy array
            settings: Dictionary of voxelization settings
        """
        # ...
    
    def compute_voxels(self, tx_points: list) -> np.ndarray:
        """
        Compute 3D voxel representation for the given transmitter points.
        
        Args:
            tx_points: List of transmitter points as (x, y) tuples
            
        Returns:
            3D voxel data as a numpy array
        """
        # ...
```

## GUI Components

### OverlayController

The overlay controller class that manages RF overlays.

```python
class OverlayController:
    def __init__(self):
        """Initialize the overlay controller."""
        # ...
    
    def register_overlay(self, name: str, overlay: callable):
        """
        Register an overlay.
        
        Args:
            name: Name of the overlay
            overlay: Overlay function
        """
        # ...
    
    def apply_overlay(self, name: str, data: np.ndarray) -> np.ndarray:
        """
        Apply an overlay to the data.
        
        Args:
            name: Name of the overlay
            data: Data to apply the overlay to
            
        Returns:
            Data with the overlay applied
        """
        # ...
```

### ExportWizard

The export wizard class that guides users through the export process.

```python
class ExportWizard:
    def __init__(self, parent: tk.Tk, overlays: dict):
        """
        Initialize the export wizard.
        
        Args:
            parent: Parent tkinter window
            overlays: Dictionary of available overlays
        """
        # ...
    
    def show(self):
        """Show the export wizard dialog."""
        # ...
    
    def export(self, overlay_name: str, filename: str):
        """
        Export the selected overlay to a file.
        
        Args:
            overlay_name: Name of the overlay to export
            filename: Path to the output file
        """
        # ...
```

## CLI Components

### cli_entrypoint

The CLI entry point function.

```python
def cli_entrypoint(argv: Sequence[str] | None = None) -> int:
    """
    Dispatch to batch runner with provided ``argv`` list.
    
    Args:
        argv: Command line arguments to pass to the batch runner
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # ...
```

### batch_main

The main function for batch processing.

```python
def main() -> int:
    """
    Run the batch processing.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # ...
```

## Physics Models

See [Physics Models Documentation](physics_models.md) for detailed information about the physics models used in the simulation.

### KernelChain

The kernel chain class that manages the physics kernels.

```python
class KernelChain:
    def __init__(self):
        """Initialize the kernel chain."""
        # ...
    
    def add_kernel(self, kernel: Kernel):
        """
        Add a kernel to the chain.
        
        Args:
            kernel: Kernel to add
        """
        # ...
    
    def process(self, dem: np.ndarray, tx_points: list, settings: dict) -> np.ndarray:
        """
        Process the DEM with the kernel chain.
        
        Args:
            dem: Digital Elevation Model as a numpy array
            tx_points: List of transmitter points as (x, y) tuples
            settings: Dictionary of processing settings
            
        Returns:
            Processed data as a numpy array
        """
        # ...
```

## Utilities

### load_dem_image

Load a DEM image from a file.

```python
def load_dem_image(path: Path) -> np.ndarray:
    """
    Load a DEM image from a file.
    
    Args:
        path: Path to the DEM image file
        
    Returns:
        DEM data as a numpy array
    """
    # ...
```

### trace_signal_path

Trace a signal path between two points.

```python
def trace_signal_path(dem: np.ndarray, tx_point: tuple, rx_point: tuple, settings: dict) -> list:
    """
    Trace a signal path between two points.
    
    Args:
        dem: Digital Elevation Model as a numpy array
        tx_point: Transmitter point as (x, y) tuple
        rx_point: Receiver point as (x, y) tuple
        settings: Dictionary of tracing settings
        
    Returns:
        List of points along the signal path
    """
    # ...
```

### plot_signal_profile

Plot a signal path profile.

```python
def plot_signal_profile(path: list, tx_height: float = 0.0) -> None:
    """
    Plot a signal path profile.
    
    Args:
        path: List of points along the signal path
        tx_height: Height of the transmitter
    """
    # ...
```
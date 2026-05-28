# OnyxGeoImage Common Workflows

This document provides step-by-step guides for common workflows in OnyxGeoImage.

## Table of Contents

1. [Basic RF Analysis](#basic-rf-analysis)
2. [3D Visualization](#3d-visualization)
3. [Path Profile Analysis](#path-profile-analysis)
4. [Exporting Results](#exporting-results)
5. [Working with Sessions](#working-with-sessions)
6. [Advanced Settings](#advanced-settings)

## Basic RF Analysis

This workflow covers the basic process of loading an image, setting transmitter points, and performing RF analysis.

### Step 1: Load an Image

1. Launch OnyxGeoImage
2. Click the "Open" button in the toolbar or use the keyboard shortcut Ctrl+O
3. Select a terrain image file (PNG, JPG, or TIFF format)
4. The image will be loaded and displayed in the main window

### Step 2: Set Transmitter Points

1. Click the "Set TX" button in the toolbar or use the keyboard shortcut Ctrl+T
2. Click on the image where you want to place the transmitter
3. You can add multiple transmitters by repeating this process
4. To remove the last transmitter, click the "Remove TX" button or use the keyboard shortcut Ctrl+Z

### Step 3: Configure Analysis Settings

1. In the settings panel on the right, adjust the following parameters:
   - TX Height: Height of the transmitter in meters
   - TX Power: Transmitter power in dBm
   - Frequency: Signal frequency in MHz
   - RX Height: Receiver height in meters
   - RX Gain: Receiver gain in dB
   - TX Gain: Transmitter gain in dB
   - Resolution: Analysis resolution in meters

2. For more accurate results, check the "High Physics" option (note: this will increase processing time)

### Step 4: Run the Analysis

1. Click the "Analyze" button in the toolbar or use the keyboard shortcut Ctrl+R
2. Wait for the analysis to complete (progress will be shown in the status bar)
3. The RF coverage overlay will be displayed on the image

### Step 5: Interpret the Results

- The color overlay represents signal strength in dBm
- Red areas indicate strong signal
- Blue areas indicate weak signal
- Black areas indicate no signal or signal below the receiver sensitivity

## 3D Visualization

This workflow covers the process of visualizing RF propagation in 3D.

### Step 1: Complete Basic RF Analysis

Follow the steps in the [Basic RF Analysis](#basic-rf-analysis) workflow to perform an RF analysis.

### Step 2: Generate 3D Voxels

1. Click the "Show Voxels" button in the toolbar or use the keyboard shortcut Ctrl+V
2. Configure the voxel settings in the dialog:
   - Voxel Height: Maximum height of the voxel space in meters
   - Voxel Layers: Number of vertical layers in the voxel space

3. Click "Generate" to create the 3D voxel representation

### Step 3: Navigate the 3D View

1. Use the slice slider to move through the vertical layers
2. Click the "Play" button to animate through the layers
3. Click the "Stop" button to stop the animation
4. Use the view mode dropdown to switch between different visualization modes:
   - Normal: Standard color overlay
   - Heatmap: Heatmap visualization
   - Contour: Contour lines visualization

### Step 4: Export 3D Results

1. Click the "Export Slice" button to export the current slice as an image
2. Click the "Export Stack" button to export all slices as a series of images

## Path Profile Analysis

This workflow covers the process of analyzing the signal path between two points.

### Step 1: Complete Basic RF Analysis

Follow the steps in the [Basic RF Analysis](#basic-rf-analysis) workflow to perform an RF analysis.

### Step 2: Generate Path Profile

1. Click the "Path Profile" button in the toolbar or use the keyboard shortcut Ctrl+P
2. Click on the image to set the starting point (usually a transmitter location)
3. Click on the image again to set the ending point (the receiver location)
4. A new window will open showing the path profile between the two points

### Step 3: Interpret the Path Profile

- The path profile shows the terrain elevation along the path
- The line of sight between the transmitter and receiver is shown
- Fresnel zones are displayed to indicate potential obstructions
- Signal strength along the path is indicated by color

## Exporting Results

This workflow covers the process of exporting analysis results.

### Step 1: Complete Basic RF Analysis

Follow the steps in the [Basic RF Analysis](#basic-rf-analysis) workflow to perform an RF analysis.

### Step 2: Export Overlay

1. Click the "Export Overlay" button in the toolbar or use the keyboard shortcut Ctrl+E
2. Select the export format (PNG, JPG, or TIFF)
3. Choose a location and filename for the exported file
4. Click "Save" to export the overlay

### Step 3: Export Raw Data

1. Click the "Export Data" button in the toolbar
2. Select the export format (CSV or NPY)
3. Choose a location and filename for the exported file
4. Click "Save" to export the raw data

### Step 4: Use the Export Wizard

1. Click the "Export Wizard" button in the toolbar
2. Select the overlay type to export
3. Configure the export options
4. Click "Export" to generate the file

## Working with Sessions

This workflow covers the process of saving and loading sessions.

### Step 1: Create a Session

1. Perform an RF analysis following the [Basic RF Analysis](#basic-rf-analysis) workflow
2. Make any adjustments to the analysis settings and transmitter locations

### Step 2: Save the Session

1. Click the "Save Session" button in the toolbar or use the keyboard shortcut Ctrl+S
2. Choose a location and filename for the session file
3. Click "Save" to save the session

### Step 3: Load a Session

1. Click the "Load Session" button in the toolbar or use the keyboard shortcut Ctrl+L
2. Select a previously saved session file
3. Click "Open" to load the session
4. The saved analysis will be restored, including transmitter locations and settings

## Advanced Settings

This workflow covers the process of configuring advanced settings for more detailed analysis.

### Step 1: Enable High Physics Mode

1. In the settings panel, check the "High Physics" option
2. This enables more accurate physics models, including:
   - Fresnel zone clearance
   - Knife-edge diffraction
   - Atmospheric refraction
   - Surface reflection
   - Weather effects

### Step 2: Configure Material Properties

1. Click the "Materials" button in the toolbar
2. Select the material type for different regions of the image
3. Adjust the material properties:
   - Permittivity: Affects signal reflection and penetration
   - Conductivity: Affects signal attenuation
   - Roughness: Affects scattering

### Step 3: Configure Weather Effects

1. Click the "Weather" button in the toolbar
2. Select the weather conditions:
   - Clear: No additional attenuation
   - Rain: Attenuation based on rain rate
   - Fog: Attenuation based on visibility
   - Snow: Attenuation based on snow rate

### Step 4: Configure Interference

1. Click the "Interference" button in the toolbar
2. Add interference sources:
   - Location: Position on the map
   - Power: Interference power in dBm
   - Frequency: Interference frequency in MHz

### Step 5: Run Advanced Analysis

1. Click the "Analyze" button to run the analysis with the advanced settings
2. The results will include the effects of the configured advanced settings
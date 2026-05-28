# Build System Documentation

This document provides comprehensive information about the build system for the OnyxGeoImage project, including setup procedures, build processes, troubleshooting guides, and verification steps.

## Table of Contents
1. [Build Environment Requirements](#build-environment-requirements)
2. [Setup Procedures](#setup-procedures)
3. [Build Processes](#build-processes)
4. [Dependency Management](#dependency-management)
5. [Build Verification](#build-verification)
6. [Troubleshooting Guide](#troubleshooting-guide)

## Build Environment Requirements

### System Requirements
- **Operating System**: Windows 10 or later (64-bit)
- **Python**: Version 3.9 or later
- **Disk Space**: At least 2GB of free disk space
- **Memory**: Minimum 4GB RAM (8GB recommended)

### Required Software
- **Python**: Download and install from [python.org](https://www.python.org/downloads/)
- **Git**: Download and install from [git-scm.com](https://git-scm.com/downloads)
- **Visual Studio Build Tools**: Required for compiling certain dependencies

### Environment Variables
The following environment variables should be set:
- `PYTHONPATH`: Should include the project's `src` directory
- `ONYX_MODE`: Set automatically by build scripts to either "full" or "lite"

## Setup Procedures

### Initial Setup
1. Clone the repository:
   ```
   git clone https://github.com/your-organization/OnyxGeoImage.git
   cd OnyxGeoImage
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Validate dependencies:
   ```
   python tools\validate_dependencies.py
   ```

### Development Environment Setup
For development, additional tools are recommended:
1. Install development dependencies:
   ```
   pip install pytest pytest-cov black isort
   ```

2. Set up pre-commit hooks:
   ```
   pip install pre-commit
   pre-commit install
   ```

## Build Processes

The project provides two build options:
1. **Lite Build**: A smaller build with core functionality
2. **Full Build**: A complete build with all features

### Lite Build
The lite build creates a smaller executable with essential features:

```
python build_lite.py
```

This script:
1. Sets the `ONYX_MODE` environment variable to "lite"
2. Runs PyInstaller with the `light.spec` specification file
3. Creates the executable in the `dist` directory

### Full Build
The full build creates a comprehensive executable with all features:

```
python build_full.py
```

This script:
1. Sets the `ONYX_MODE` environment variable to "full"
2. Runs PyInstaller with the `full.spec` specification file
3. Creates the executable in the `dist` directory

### Build and Package
For a complete build and packaging process:

```
build_and_package.bat
```

This batch file:
1. Cleans previous build artifacts
2. Runs tests
3. Builds both lite and full versions
4. Creates distribution packages

## Dependency Management

### Requirements Files
The project uses several requirements files:
- `requirements.txt`: Main requirements file with all dependencies
- `requirements-runtime.txt`: Runtime-only dependencies
- `requirements_lock.txt`: Locked versions of all dependencies

### Dependency Validation
To validate that all required dependencies are installed with correct versions:

```
python tools\validate_dependencies.py
```

This script:
1. Checks if all required packages are installed
2. Verifies that installed versions match the required versions
3. Ensures critical dependencies have pinned versions
4. Offers to install missing or update outdated dependencies

### Critical Dependencies
The following dependencies are critical for the build process and must have pinned versions:
- pyinstaller
- numpy
- matplotlib
- rasterio
- xarray
- onnxruntime
- PySide6

## Build Verification

### Verification Steps
After building, verify the build was successful:

1. Check that the executable exists in the `dist` directory
2. Verify the executable has a reasonable file size (at least 1MB)
3. Run the executable with the `--version` flag to ensure it works
4. Run automated verification tests:
   ```
   python -m pytest tests\test_build_scripts.py::test_executable_integrity
   ```

### Success Criteria
A successful build meets the following criteria:
1. Build process completes without errors
2. Executable is created in the `dist` directory
3. Executable runs without crashing
4. All verification tests pass
5. The application displays the correct version information

### Automated Verification
The project includes automated verification tests in `tests\test_build_scripts.py` that check:
1. The build process sets the correct environment variables
2. PyInstaller is called with the correct parameters
3. The build process handles errors appropriately
4. The built executable exists and has a reasonable size
5. The executable can be run with basic parameters

## Troubleshooting Guide

### Common Issues and Solutions

#### PyInstaller Not Found
**Issue**: `PyInstaller not found` error when running build scripts.

**Solution**:
1. Ensure PyInstaller is installed: `pip install pyinstaller`
2. Verify the virtual environment is activated
3. Check if PyInstaller is in your PATH

#### Missing Dependencies
**Issue**: Build fails due to missing dependencies.

**Solution**:
1. Run the dependency validation script: `python tools\validate_dependencies.py`
2. Install any missing dependencies: `pip install -r requirements.txt`
3. Check for any version conflicts

#### Spec File Not Found
**Issue**: Build fails because the spec file is not found.

**Solution**:
1. Ensure you're running the build script from the project root directory
2. Verify that the spec file exists (`light.spec` or `full.spec`)
3. If missing, recreate the spec file: `pyinstaller --name=onyx_geo_image src\main.py`

#### Build Produces No Artifacts
**Issue**: Build completes but no executable is created.

**Solution**:
1. Check the PyInstaller output for errors
2. Verify that the `dist` directory exists and has write permissions
3. Try cleaning the build directories: `rmdir /s /q build dist`
4. Run PyInstaller with the `--clean` flag

#### Executable Crashes on Startup
**Issue**: The built executable crashes immediately when run.

**Solution**:
1. Run the executable from the command line to see error messages
2. Check if all required DLLs are included in the distribution
3. Verify that all dependencies are correctly specified in the spec file
4. Try running with the `--debug` flag: `onyx_geo_image.exe --debug`

#### Out of Memory During Build
**Issue**: Build process runs out of memory.

**Solution**:
1. Close other memory-intensive applications
2. Increase virtual memory allocation
3. Try building on a machine with more RAM
4. Split the build process into smaller steps

### Getting Help
If you encounter issues not covered in this guide:
1. Check the project's issue tracker for similar problems
2. Review the PyInstaller documentation
3. Contact the development team with detailed information about the issue
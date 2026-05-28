"""Batch CLI for RF analysis."""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np

from sim_rf_map.logging_config import configure_logging
from sim_rf_map.startup_manager import (
    load_resource, log_startup_diagnostic, save_startup_report, 
    register_optional_component
)
from sim_rf_map.config_validator import (
    load_config_with_validation, validate_float_range,
    validate_string_choice
)
from sim_rf_map.crash_recovery import (
    CrashHandler, create_crash_dump
)

# Configure logging system
configure_logging(level=logging.INFO)

# Default configuration values
DEFAULT_CONFIG = {
    "simulation": {
        "default_frequency_mhz": 900.0,
        "default_polarization": "vertical",
        "default_temperature_c": 20.0,
        "default_humidity_percent": 50.0,
        "default_pressure_hpa": 1013.25,
        "default_path_length_km": 1.0,
        "default_cloud_cover": "None",
        "default_precipitation": "None"
    },
    "output": {
        "default_output_dir": "outputs",
        "export_npy": True,
        "export_png": True
    }
}


class ValidationResult(tuple):
    def __new__(cls, is_valid: bool, error_messages: list):
        return super().__new__(cls, (is_valid, error_messages))

    @property
    def is_valid(self) -> bool:
        return self[0]

    @property
    def error_messages(self) -> list:
        return self[1]

    def __bool__(self) -> bool:
        return bool(self.is_valid)


class _BasicPropagator:
    def compute_coverage(self, dem: np.ndarray, _tx_points: list, _settings: Dict[str, Any]) -> np.ndarray:
        return np.zeros_like(dem, dtype=float)


def get_propagator(_settings: Optional[Dict[str, Any]] = None) -> _BasicPropagator:
    return _BasicPropagator()


def _unpack_validation_result(result: Any) -> Tuple[bool, list]:
    if isinstance(result, tuple):
        return bool(result[0]), list(result[1])
    return bool(result), []


def _run_legacy_coverage_cli(args: argparse.Namespace) -> int:
    import matplotlib.pyplot as plt

    dem = load_dem_image(Path(args.dem))
    tx_points = [
        {
            "lat": args.tx_lat,
            "lon": args.tx_lon,
            "height": args.tx_height,
            "power": getattr(args, "tx_power", None),
        }
    ]
    settings = vars(args).copy()

    propagator = get_propagator()
    coverage = propagator.compute_coverage(dem, tx_points, settings)

    output_path = Path(args.output)
    if output_path.parent != Path("."):
        output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path.with_suffix(".npy"), coverage)
    plt.imsave(output_path, coverage, cmap="viridis")
    return 0


def load_dem_image(path: Path) -> np.ndarray:
    """
    Load grayscale DEM and normalize to 0-1.

    Args:
        path: Path to the DEM image

    Returns:
        Normalized DEM array
    """
    log_startup_diagnostic("dem_loading", "info", f"Loading DEM image from: {path}")

    try:
        from PIL import Image

        if not path.exists():
            raise FileNotFoundError(f"DEM image not found: {path}")

        img = Image.open(path).convert("L")
        dem = np.array(img).astype(np.float32)
        dem -= dem.min()

        log_startup_diagnostic("dem_loading", "success", f"DEM image loaded with shape: {dem.shape}")
        return dem
    except Exception as e:
        log_startup_diagnostic("dem_loading", "error", f"Failed to load DEM image: {str(e)}")
        raise


def validate_cli_args(args: argparse.Namespace) -> ValidationResult:
    """
    Validate command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Tuple of (is_valid, error_messages)
    """
    is_valid = True
    error_messages = []

    input_file = getattr(args, "input", None) or getattr(args, "dem", None)

    # Validate input file
    if not input_file or not Path(input_file).exists():
        is_valid = False
        error_messages.append(f"Input file not found: {input_file}")

    if hasattr(args, "tx_lat"):
        tx_lat_valid, tx_lat_error = validate_float_range(-90.0, 90.0)(args.tx_lat)
        if not tx_lat_valid:
            is_valid = False
            error_messages.append(f"Invalid transmitter latitude: {tx_lat_error}")

    if hasattr(args, "tx_lon"):
        tx_lon_valid, tx_lon_error = validate_float_range(-180.0, 180.0)(args.tx_lon)
        if not tx_lon_valid:
            is_valid = False
            error_messages.append(f"Invalid transmitter longitude: {tx_lon_error}")

    if hasattr(args, "tx_height"):
        tx_height_valid, tx_height_error = validate_float_range(0.0, 10000.0)(args.tx_height)
        if not tx_height_valid or float(args.tx_height) <= 0:
            is_valid = False
            error_messages.append(f"Invalid transmitter height: {tx_height_error or 'Value must be positive'}")

    # Validate frequency
    freq_valid, freq_error = validate_float_range(100.0, 6000.0)(args.frequency)
    if not freq_valid:
        is_valid = False
        error_messages.append(f"Invalid frequency: {freq_error}")

    # Validate cloud cover
    cloud_valid, cloud_error = validate_string_choice(["None", "Light", "Medium", "Heavy"])(
        getattr(args, "cloud", DEFAULT_CONFIG["simulation"]["default_cloud_cover"])
    )
    if not cloud_valid:
        is_valid = False
        error_messages.append(f"Invalid cloud cover: {cloud_error}")

    # Validate precipitation
    rain_valid, rain_error = validate_string_choice(["None", "Light", "Medium", "Heavy"])(
        getattr(args, "rain", DEFAULT_CONFIG["simulation"]["default_precipitation"])
    )
    if not rain_valid:
        is_valid = False
        error_messages.append(f"Invalid precipitation: {rain_error}")

    # Validate path length
    path_length_valid, path_length_error = validate_float_range(0.1, 100.0)(
        getattr(args, "path_length", DEFAULT_CONFIG["simulation"]["default_path_length_km"])
    )
    if not path_length_valid:
        is_valid = False
        error_messages.append(f"Invalid path length: {path_length_error}")

    # Validate temperature
    temp_valid, temp_error = validate_float_range(-50.0, 50.0)(
        getattr(args, "temperature", DEFAULT_CONFIG["simulation"]["default_temperature_c"])
    )
    if not temp_valid:
        is_valid = False
        error_messages.append(f"Invalid temperature: {temp_error}")

    # Validate humidity
    humidity_valid, humidity_error = validate_float_range(0.0, 100.0)(
        getattr(args, "humidity", DEFAULT_CONFIG["simulation"]["default_humidity_percent"])
    )
    if not humidity_valid:
        is_valid = False
        error_messages.append(f"Invalid humidity: {humidity_error}")

    # Validate pressure
    pressure_valid, pressure_error = validate_float_range(800.0, 1100.0)(
        getattr(args, "pressure", DEFAULT_CONFIG["simulation"]["default_pressure_hpa"])
    )
    if not pressure_valid:
        is_valid = False
        error_messages.append(f"Invalid pressure: {pressure_error}")

    # Validate polarization
    polarization_valid, polarization_error = validate_string_choice(["horizontal", "vertical"])(
        getattr(args, "polarization", DEFAULT_CONFIG["simulation"]["default_polarization"])
    )
    if not polarization_valid:
        is_valid = False
        error_messages.append(f"Invalid polarization: {polarization_error}")

    return ValidationResult(is_valid, error_messages)


def main() -> int:
    """
    Execute batch RF propagation.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    start_time = time.time()
    log_startup_diagnostic("batch_cli", "info", "Starting batch RF propagation CLI")

    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Batch RF Propagation CLI")
        parser.add_argument("--input", "--dem", dest="input", required=True, help="Path to DEM image (grayscale)")
        parser.add_argument("--frequency", type=float, default=DEFAULT_CONFIG["simulation"]["default_frequency_mhz"], 
                          help="Frequency MHz")
        parser.add_argument("--output", default=DEFAULT_CONFIG["output"]["default_output_dir"], 
                          help="Output directory")
        parser.add_argument("--config", help="Path to configuration file")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")

        # Add weather attenuation options
        parser.add_argument("--cloud", choices=["None", "Light", "Medium", "Heavy"], 
                          default=DEFAULT_CONFIG["simulation"]["default_cloud_cover"],
                          help="Cloud cover level for attenuation calculation")
        parser.add_argument("--rain", choices=["None", "Light", "Medium", "Heavy"], 
                          default=DEFAULT_CONFIG["simulation"]["default_precipitation"],
                          help="Precipitation level for attenuation calculation")
        parser.add_argument("--path-length", type=float, 
                          default=DEFAULT_CONFIG["simulation"]["default_path_length_km"],
                          help="Path length through weather in kilometers")
        parser.add_argument("--temperature", type=float, 
                          default=DEFAULT_CONFIG["simulation"]["default_temperature_c"],
                          help="Temperature in Celsius")
        parser.add_argument("--humidity", type=float, 
                          default=DEFAULT_CONFIG["simulation"]["default_humidity_percent"],
                          help="Relative humidity in percent")
        parser.add_argument("--pressure", type=float, 
                          default=DEFAULT_CONFIG["simulation"]["default_pressure_hpa"],
                          help="Atmospheric pressure in hPa")
        parser.add_argument("--polarization", choices=["horizontal", "vertical"], 
                          default=DEFAULT_CONFIG["simulation"]["default_polarization"],
                          help="Signal polarization")

        args = parser.parse_args()
        log_startup_diagnostic("argument_parsing", "success", f"Arguments parsed: {args}")

        # Set up debug logging if requested
        if getattr(args, "debug", False):
            from sim_rf_map.logging_config import enable_dev_logging
            enable_dev_logging()
            log_startup_diagnostic("logging", "info", "Debug logging enabled")

        # Validate command line arguments
        args_valid, error_messages = _unpack_validation_result(validate_cli_args(args))
        if not args_valid:
            for error in error_messages:
                logging.error(error)
            log_startup_diagnostic("argument_validation", "error", f"Invalid arguments: {'; '.join(error_messages)}")
            return 1

        log_startup_diagnostic("argument_validation", "success", "Arguments validated successfully")

        if hasattr(args, "dem") and not hasattr(args, "input"):
            return _run_legacy_coverage_cli(args)

        # Load configuration if provided
        config = DEFAULT_CONFIG
        if args.config:
            config_path = Path(args.config)
            try:
                loaded_config, warnings = load_config_with_validation(config_path)
                if warnings:
                    log_startup_diagnostic(
                        "configuration", 
                        "warning", 
                        f"Configuration loaded with warnings: {'; '.join(warnings)}"
                    )
                else:
                    log_startup_diagnostic("configuration", "success", "Configuration loaded successfully")

                # Merge loaded config with defaults
                for section in DEFAULT_CONFIG:
                    if section in loaded_config:
                        config[section].update(loaded_config[section])
            except Exception as e:
                log_startup_diagnostic("configuration", "warning", f"Failed to load configuration: {str(e)}")
                logging.warning(f"Failed to load configuration from {config_path}: {e}")
                logging.warning("Using default configuration")

        # Load required modules
        with CrashHandler(component="module_loading"):
            log_startup_diagnostic("module_loading", "info", "Loading required modules")

            from sim_rf_map.weather_model import WeatherConditions
            from sim_rf_map.wavefront_propagator import propagate_wavefront
            from sim_rf_map.voxelizer import voxelize_dem
            from sim_rf_map.material_inference import classify_material, get_voxel_permeability
            from sim_rf_map.export_tools import export_loss_npy, export_loss_png

            log_startup_diagnostic("module_loading", "success", "Required modules loaded successfully")

        # Create output directory
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        log_startup_diagnostic("output_directory", "success", f"Output directory created: {output_path}")

        # Load DEM image
        dem = load_resource("dem_image", load_dem_image, Path(args.input))

        # Progressive resource loading with diagnostics
        with CrashHandler(component="voxelization"):
            log_startup_diagnostic("voxelization", "info", "Voxelizing DEM")
            voxels = load_resource("voxels", voxelize_dem, dem)
            log_startup_diagnostic("voxelization", "success", f"Voxel volume created with shape: {voxels.shape}")

        with CrashHandler(component="material_classification"):
            log_startup_diagnostic("material_classification", "info", "Classifying materials")
            materials = load_resource("materials", classify_material, np.stack([dem] * 3, axis=2))
            log_startup_diagnostic("material_classification", "success", "Materials classified successfully")

        # Optional component: permeability calculation
        try:
            log_startup_diagnostic("permeability", "info", "Calculating voxel permeability")
            perm2d = load_resource("permeability_2d", get_voxel_permeability, materials, optional=True)

            if perm2d is not None:
                permeability = np.repeat(perm2d[None, :, :], voxels.shape[0], axis=0)
                log_startup_diagnostic("permeability", "success", f"Permeability matrix created with shape: {permeability.shape}")
                register_optional_component("permeability", True)
            else:
                permeability = None
                log_startup_diagnostic("permeability", "warning", "Permeability calculation skipped")
                register_optional_component("permeability", False)
        except Exception as e:
            log_startup_diagnostic("permeability", "warning", f"Failed to calculate permeability: {str(e)}")
            logging.warning(f"Failed to calculate permeability: {e}")
            permeability = None
            register_optional_component("permeability", False)

        # Set up origin point
        origin = (int(1.65), dem.shape[0] // 2, dem.shape[1] // 2)
        log_startup_diagnostic("origin", "success", f"Using origin point: {origin}")

        # Initialize weather conditions
        with CrashHandler(component="weather"):
            log_startup_diagnostic("weather", "info", "Initializing weather conditions")

            weather = WeatherConditions(
                temperature_c=args.temperature,
                humidity_percent=args.humidity,
                precipitation_level=args.rain,
                cloud_cover_level=args.cloud,
                pressure_hpa=args.pressure,
                path_length_km=args.path_length
            )

            log_startup_diagnostic("weather", "success", "Weather conditions initialized successfully")

            # Log weather attenuation settings
            log_startup_diagnostic(
                "weather_settings", 
                "info", 
                f"Weather settings: cloud={args.cloud}, rain={args.rain}, path_length={args.path_length}km"
            )
            log_startup_diagnostic(
                "atmospheric_conditions", 
                "info", 
                f"Atmospheric conditions: temp={args.temperature}°C, humidity={args.humidity}%, pressure={args.pressure}hPa"
            )

            # Calculate expected weather attenuation for reference
            freq_GHz = args.frequency / 1000.0  # Convert MHz to GHz
            if args.cloud != "None" or args.rain != "None":
                sample_loss = 100.0  # Example loss value in dB
                attenuated_loss = weather.apply_weather_attenuation(
                    sample_loss, freq_GHz, args.polarization
                )
                weather_attenuation = attenuated_loss - sample_loss
                log_startup_diagnostic(
                    "weather_attenuation", 
                    "info", 
                    f"Expected weather attenuation: {weather_attenuation:.2f} dB"
                )

        # Propagate wavefront
        with CrashHandler(component="propagation"):
            log_startup_diagnostic("propagation", "info", f"Propagating wavefront at {args.frequency}MHz")

            loss_map = propagate_wavefront(
                voxels=voxels,
                materials=materials,
                permeability=permeability,
                origin=origin,
                frequency_mhz=args.frequency,
                weather=weather,
                polarization=args.polarization,
            )

            log_startup_diagnostic("propagation", "success", f"Loss map generated with shape: {loss_map.shape}")

        # Export results
        with CrashHandler(component="export"):
            # Export NPY
            if config["output"].get("export_npy", True):
                log_startup_diagnostic("export_npy", "info", f"Exporting NPY loss map to: {args.output}")
                export_loss_npy(loss_map, args.output)
                log_startup_diagnostic("export_npy", "success", "NPY loss map exported successfully")

            # Export PNG
            if config["output"].get("export_png", True):
                log_startup_diagnostic("export_png", "info", f"Exporting PNG loss map to: {args.output}")
                export_loss_png(loss_map[origin[0]], args.output)
                log_startup_diagnostic("export_png", "success", "PNG loss map exported successfully")

        # Generate startup report
        elapsed_time = time.time() - start_time
        log_startup_diagnostic(
            "batch_cli", 
            "success", 
            f"Batch RF propagation completed successfully in {elapsed_time:.2f} seconds"
        )
        save_startup_report()

        return 0
    except Exception as e:
        # Log the exception
        log_startup_diagnostic("batch_cli", "error", f"Batch RF propagation failed: {str(e)}")
        logging.exception("Batch RF propagation failed")

        # Create crash dump
        create_crash_dump(e, "batch_cli")

        # Generate startup report
        save_startup_report()

        return 1


if __name__ == "__main__":
    sys.exit(main())

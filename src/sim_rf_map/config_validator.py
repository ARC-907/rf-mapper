"""Configuration validation and repair utilities."""

import logging
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Set

# Dictionary to store default configuration values
_default_config_values = {}
# Dictionary to store configuration validation rules
_config_validation_rules = {}
# Set to store required configuration parameters
_required_config_params = set()


def register_config_defaults(config_section: str, defaults: Dict[str, Any]) -> None:
    """
    Register default values for a configuration section.
    
    Args:
        config_section: Name of the configuration section
        defaults: Dictionary of default values for the section
    """
    if config_section not in _default_config_values:
        _default_config_values[config_section] = {}
    
    _default_config_values[config_section].update(defaults)
    logging.debug(f"Registered default values for config section: {config_section}")


def register_config_validation(config_section: str, param_name: str, 
                              validation_func: callable, required: bool = False) -> None:
    """
    Register a validation function for a configuration parameter.
    
    Args:
        config_section: Name of the configuration section
        param_name: Name of the parameter to validate
        validation_func: Function that takes a value and returns (is_valid, error_message)
        required: Whether the parameter is required
    """
    if config_section not in _config_validation_rules:
        _config_validation_rules[config_section] = {}
    
    _config_validation_rules[config_section][param_name] = validation_func
    
    if required:
        _required_config_params.add((config_section, param_name))
    
    logging.debug(f"Registered validation for config parameter: {config_section}.{param_name}")


def validate_config(config: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, Dict[str, Any]]]:
    """
    Validate a configuration dictionary against registered rules.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_messages, repaired_config)
    """
    is_valid = True
    error_messages = []
    repaired_config = {}
    
    # Copy the original config to avoid modifying it
    for section, params in config.items():
        repaired_config[section] = params.copy()
    
    # Check for required parameters
    for section, param in _required_config_params:
        if section not in config or param not in config[section]:
            is_valid = False
            error_messages.append(f"Missing required parameter: {section}.{param}")
            
            # Add default value if available
            if section in _default_config_values and param in _default_config_values[section]:
                if section not in repaired_config:
                    repaired_config[section] = {}
                repaired_config[section][param] = _default_config_values[section][param]
                error_messages.append(f"Using default value for {section}.{param}: {_default_config_values[section][param]}")
    
    # Validate parameters against rules
    for section, params in config.items():
        if section in _config_validation_rules:
            for param, value in params.items():
                if param in _config_validation_rules[section]:
                    validation_func = _config_validation_rules[section][param]
                    param_valid, error_msg = validation_func(value)
                    
                    if not param_valid:
                        is_valid = False
                        error_messages.append(f"Invalid value for {section}.{param}: {error_msg}")
                        
                        # Use default value if available
                        if section in _default_config_values and param in _default_config_values[section]:
                            repaired_config[section][param] = _default_config_values[section][param]
                            error_messages.append(f"Using default value for {section}.{param}: {_default_config_values[section][param]}")
    
    # Add missing sections and parameters with default values
    for section, defaults in _default_config_values.items():
        if section not in repaired_config:
            repaired_config[section] = {}
        
        for param, default_value in defaults.items():
            if param not in repaired_config[section]:
                repaired_config[section][param] = default_value
                error_messages.append(f"Added missing parameter {section}.{param} with default value: {default_value}")
    
    return is_valid, error_messages, repaired_config


def load_config_with_validation(config_path: Path) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Load and validate a configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Tuple of (validated_config, warning_messages)
    """
    warnings = []
    
    try:
        if not config_path.exists():
            warnings.append(f"Configuration file not found: {config_path}")
            config = {}
        else:
            with open(config_path, 'r') as f:
                config = json.load(f)
    except Exception as e:
        warnings.append(f"Error loading configuration file: {e}")
        config = {}
    
    is_valid, validation_warnings, repaired_config = validate_config(config)
    warnings.extend(validation_warnings)
    
    if not is_valid:
        warnings.append("Configuration validation failed, using repaired configuration")
    
    return repaired_config, warnings


def save_config(config: Dict[str, Dict[str, Any]], config_path: Path) -> None:
    """
    Save a configuration dictionary to a file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save the configuration to
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    logging.info(f"Configuration saved to {config_path}")


def repair_config_file(config_path: Path) -> Tuple[bool, List[str]]:
    """
    Repair a configuration file by loading it, validating it, and saving the repaired version.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Tuple of (success, messages)
    """
    try:
        repaired_config, warnings = load_config_with_validation(config_path)
        
        # Create a backup of the original file if it exists
        if config_path.exists():
            backup_path = config_path.with_suffix(f"{config_path.suffix}.bak")
            config_path.rename(backup_path)
            warnings.append(f"Created backup of original configuration at {backup_path}")
        
        # Save the repaired configuration
        save_config(repaired_config, config_path)
        warnings.append(f"Repaired configuration saved to {config_path}")
        
        return True, warnings
    except Exception as e:
        return False, [f"Failed to repair configuration: {e}"]


# Common validation functions
def validate_int_range(min_val: int, max_val: int):
    """Create a validator for an integer range."""
    def validator(value):
        try:
            int_val = int(value)
            if min_val <= int_val <= max_val:
                return True, ""
            else:
                return False, f"Value must be between {min_val} and {max_val}"
        except (ValueError, TypeError):
            return False, "Value must be an integer"
    return validator


def validate_float_range(min_val: float, max_val: float):
    """Create a validator for a float range."""
    def validator(value):
        try:
            float_val = float(value)
            if min_val <= float_val <= max_val:
                return True, ""
            else:
                return False, f"Value must be between {min_val} and {max_val}"
        except (ValueError, TypeError):
            return False, "Value must be a number"
    return validator


def validate_string_choice(valid_choices: List[str]):
    """Create a validator for a string choice."""
    def validator(value):
        if value in valid_choices:
            return True, ""
        else:
            return False, f"Value must be one of: {', '.join(valid_choices)}"
    return validator


def validate_path_exists():
    """Create a validator that checks if a path exists."""
    def validator(value):
        try:
            path = Path(value)
            if path.exists():
                return True, ""
            else:
                return False, f"Path does not exist: {path}"
        except Exception:
            return False, "Invalid path format"
    return validator


# Register common configuration defaults
register_config_defaults("logging", {
    "level": "INFO",
    "include_console": True,
    "log_dir": str(Path.home() / "logs" / "sim_rf_map"),
    "max_log_files": 10,
    "max_log_size_mb": 10
})

register_config_defaults("display", {
    "width": 1024,
    "height": 768,
    "fullscreen": False,
    "theme": "default"
})

register_config_defaults("processing", {
    "threads": 4,
    "max_memory_mb": 1024,
    "use_gpu": False
})

register_config_defaults("simulation", {
    "default_frequency_mhz": 900.0,
    "default_polarization": "vertical",
    "default_temperature_c": 20.0,
    "default_humidity_percent": 50.0,
    "default_pressure_hpa": 1013.25
})

# Register common validation rules
register_config_validation("logging", "level", 
                          validate_string_choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]))
register_config_validation("logging", "include_console", lambda v: (isinstance(v, bool), "Must be a boolean"))
register_config_validation("logging", "max_log_files", validate_int_range(1, 100))
register_config_validation("logging", "max_log_size_mb", validate_int_range(1, 1000))

register_config_validation("display", "width", validate_int_range(640, 3840))
register_config_validation("display", "height", validate_int_range(480, 2160))
register_config_validation("display", "fullscreen", lambda v: (isinstance(v, bool), "Must be a boolean"))
register_config_validation("display", "theme", 
                          validate_string_choice(["default", "dark", "light", "high_contrast"]))

register_config_validation("processing", "threads", validate_int_range(1, 32))
register_config_validation("processing", "max_memory_mb", validate_int_range(256, 32768))
register_config_validation("processing", "use_gpu", lambda v: (isinstance(v, bool), "Must be a boolean"))

register_config_validation("simulation", "default_frequency_mhz", validate_float_range(100.0, 6000.0))
register_config_validation("simulation", "default_polarization", 
                          validate_string_choice(["horizontal", "vertical"]))
register_config_validation("simulation", "default_temperature_c", validate_float_range(-50.0, 50.0))
register_config_validation("simulation", "default_humidity_percent", validate_float_range(0.0, 100.0))
register_config_validation("simulation", "default_pressure_hpa", validate_float_range(800.0, 1100.0))
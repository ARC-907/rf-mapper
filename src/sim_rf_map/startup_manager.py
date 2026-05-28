"""Startup sequence manager for progressive resource loading and diagnostics."""

import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple

# Dictionary to store loaded resources
_loaded_resources = {}
# Dictionary to store resource loading times
_resource_loading_times = {}
# List to store startup diagnostics
_startup_diagnostics = []
# Dictionary to store optional components status
_optional_components = {}


def log_startup_diagnostic(component: str, status: str, details: Optional[str] = None) -> None:
    """
    Log a startup diagnostic entry.
    
    Args:
        component: Name of the component being initialized
        status: Status of the initialization (success, warning, error)
        details: Optional details about the initialization
    """
    timestamp = time.time()
    diagnostic = {
        "timestamp": timestamp,
        "component": component,
        "status": status,
        "details": details
    }
    _startup_diagnostics.append(diagnostic)
    
    # Log the diagnostic
    if status == "success":
        logging.info(f"Startup: {component} initialized successfully")
    elif status == "warning":
        logging.warning(f"Startup: {component} initialized with warnings: {details}")
    elif status == "error":
        logging.error(f"Startup: {component} failed to initialize: {details}")
    else:
        logging.info(f"Startup: {component} - {status}: {details}")


def get_startup_diagnostics() -> List[Dict]:
    """Get the list of startup diagnostics."""
    return _startup_diagnostics


def load_resource(resource_name: str, loader_func: Callable, *args, optional: bool = False, **kwargs) -> Any:
    """
    Load a resource with diagnostics and timing.
    
    Args:
        resource_name: Name of the resource to load
        loader_func: Function to call to load the resource
        *args: Arguments to pass to the loader function
        optional: Whether the resource is optional
        **kwargs: Keyword arguments to pass to the loader function
        
    Returns:
        The loaded resource or None if loading failed and the resource is optional
    """
    if resource_name in _loaded_resources:
        return _loaded_resources[resource_name]
    
    logging.info(f"Loading resource: {resource_name}")
    start_time = time.time()
    
    try:
        resource = loader_func(*args, **kwargs)
        end_time = time.time()
        loading_time = end_time - start_time
        
        _loaded_resources[resource_name] = resource
        _resource_loading_times[resource_name] = loading_time
        
        log_startup_diagnostic(
            resource_name, 
            "success", 
            f"Loaded in {loading_time:.2f} seconds"
        )
        
        if optional:
            _optional_components[resource_name] = True
            
        return resource
    except Exception as e:
        end_time = time.time()
        loading_time = end_time - start_time
        
        error_details = f"{str(e)}\n{traceback.format_exc()}"
        log_startup_diagnostic(
            resource_name, 
            "error" if not optional else "warning", 
            f"Failed to load in {loading_time:.2f} seconds: {error_details}"
        )
        
        if optional:
            _optional_components[resource_name] = False
            return None
        else:
            raise


def register_optional_component(component_name: str, status: bool) -> None:
    """
    Register an optional component's status.
    
    Args:
        component_name: Name of the component
        status: Whether the component initialized successfully
    """
    _optional_components[component_name] = status
    log_startup_diagnostic(
        component_name,
        "success" if status else "warning",
        "Optional component registered" if status else "Optional component not available"
    )


def is_component_available(component_name: str) -> bool:
    """
    Check if an optional component is available.
    
    Args:
        component_name: Name of the component to check
        
    Returns:
        True if the component is available, False otherwise
    """
    return _optional_components.get(component_name, False)


def get_resource_loading_times() -> Dict[str, float]:
    """Get the dictionary of resource loading times."""
    return _resource_loading_times


def get_loaded_resources() -> Dict[str, Any]:
    """Get the dictionary of loaded resources."""
    return _loaded_resources


def generate_startup_report() -> str:
    """
    Generate a detailed startup report.
    
    Returns:
        A string containing the startup report
    """
    report = ["=== STARTUP DIAGNOSTICS REPORT ==="]
    report.append(f"Python version: {sys.version}")
    report.append(f"Platform: {sys.platform}")
    report.append(f"Command: {' '.join(sys.argv)}")
    report.append(f"Working directory: {os.getcwd()}")
    report.append("")
    
    report.append("--- Resource Loading Times ---")
    for resource, loading_time in _resource_loading_times.items():
        report.append(f"{resource}: {loading_time:.2f} seconds")
    report.append("")
    
    report.append("--- Optional Components ---")
    for component, status in _optional_components.items():
        report.append(f"{component}: {'Available' if status else 'Not Available'}")
    report.append("")
    
    report.append("--- Startup Sequence ---")
    for diagnostic in _startup_diagnostics:
        timestamp = diagnostic["timestamp"]
        component = diagnostic["component"]
        status = diagnostic["status"]
        details = diagnostic["details"] or ""
        
        report.append(f"[{status.upper()}] {component}: {details}")
    
    return "\n".join(report)


def save_startup_report(file_path: Optional[Path] = None) -> Path:
    """
    Save the startup report to a file.
    
    Args:
        file_path: Path to save the report to. If None, a default path is used.
        
    Returns:
        The path where the report was saved
    """
    if file_path is None:
        from sim_rf_map.logging_config import LOGS_DIR
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = LOGS_DIR / f"{timestamp}_startup_report.txt"
    
    report = generate_startup_report()
    file_path.write_text(report)
    logging.info(f"Startup report saved to {file_path}")
    
    return file_path
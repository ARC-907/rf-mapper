import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sim_rf_map.logging_config import configure_logging

def test_logging_system():
    """Test that the logging system creates log files in the top-level logs directory."""
    # Configure logging
    configure_logging(level=logging.INFO)
    
    # Log some messages
    logging.info("Test log message 1")
    logging.warning("Test log message 2")
    logging.error("Test log message 3")
    
    # Check if the logs directory exists
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    assert logs_dir.exists(), f"Logs directory not found at {logs_dir}"
    
    # Check if at least one log file exists
    log_files = list(logs_dir.glob("*.log"))
    assert len(log_files) > 0, f"No log files found in {logs_dir}"
    
    # Print the log files for verification
    print(f"Found {len(log_files)} log files in {logs_dir}:")
    for log_file in log_files:
        print(f"  - {log_file.name}")
    
    print("Logging system test passed!")

if __name__ == "__main__":
    test_logging_system()
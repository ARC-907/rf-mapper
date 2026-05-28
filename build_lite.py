import os
import subprocess
import sys
import logging
from pathlib import Path
import pytest
import coverage
from sim_rf_map.stability_metrics import generate_stability_report

# Configure logging
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/build_lite.log', mode='w')
    ]
)
logger = logging.getLogger('build_lite')

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        __import__("PyInstaller")
        logger.info("PyInstaller is installed.")
        return True
    except ImportError:
        logger.error("PyInstaller is not installed. Please install it with 'pip install pyinstaller'.")
        return False

def run_tests_with_coverage():
    """Run tests and check coverage before building."""
    logger.info("Running tests with coverage...")

    # Create a coverage object
    cov = coverage.Coverage(source=['src/sim_rf_map'])

    try:
        # Start coverage measurement
        cov.start()

        # Run tests
        logger.info("Running pytest...")
        result = pytest.main(['tests'])

        # Stop coverage measurement
        cov.stop()

        # Generate coverage report
        cov.save()
        cov.report()

        # Get coverage percentage
        coverage_data = cov.get_data()
        total_lines = 0
        covered_lines = 0

        for filename in coverage_data.measured_files():
            # Skip files in site-packages
            if 'site-packages' in filename:
                continue

            try:
                _, statements, _, missing_lines, _ = cov.analysis2(filename)
            except coverage.CoverageException:
                continue

            total_lines += len(statements)
            covered_lines += len(statements) - len(missing_lines)

        if total_lines > 0:
            coverage_percentage = (covered_lines / total_lines) * 100
            logger.info(f"Test coverage: {coverage_percentage:.2f}%")

            if coverage_percentage < 70:
                logger.warning(
                    f"Test coverage ({coverage_percentage:.2f}%) is below the portfolio target (70%). Continuing build."
                )
        else:
            logger.warning("No lines were measured for coverage.")
            coverage_percentage = 0

        # Check if tests passed
        if result != 0:
            logger.error("Tests failed. Build aborted.")
            return False, coverage_percentage

        logger.info("All tests passed.")
        return True, coverage_percentage

    except Exception as e:
        logger.error(f"An error occurred while running tests: {str(e)}")
        return False, 0

def check_spec_file():
    """Check if the spec file exists."""
    spec_file = Path("light.spec")
    if spec_file.exists():
        logger.info(f"Spec file found: {spec_file}")
        return True
    else:
        logger.error(f"Spec file not found: {spec_file}")
        return False

def build():
    """Run the build process with error handling."""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    logger.info("Starting lite build process...")

    # Set environment variable
    os.environ["ONYX_MODE"] = "lite"
    logger.info("Set ONYX_MODE=lite")

    # Check dependencies and spec file
    if not check_dependencies() or not check_spec_file():
        logger.error("Build prerequisites not met. Exiting.")
        return False

    # Run tests and check coverage
    tests_passed, coverage_percentage = run_tests_with_coverage()
    if not tests_passed:
        logger.error("Tests failed. Build aborted.")
        return False

    logger.info(f"Tests passed with {coverage_percentage:.2f}% coverage. Proceeding with build.")

    # Generate stability report
    logger.info("Generating stability report...")
    report_path = generate_stability_report()
    if report_path:
        logger.info(f"Stability report generated: {report_path}")
    else:
        logger.warning("Failed to generate stability report, but continuing with build.")

    # Run PyInstaller
    try:
        logger.info("Running PyInstaller with light.spec...")
        result = subprocess.run(
            ["pyinstaller", "light.spec"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        logger.info("PyInstaller completed successfully.")
        logger.debug(f"PyInstaller stdout: {result.stdout}")

        # Verify build output
        dist_path = Path("dist")
        if dist_path.exists() and any(dist_path.iterdir()):
            logger.info("Build artifacts found in dist directory.")
            return True
        else:
            logger.error("No build artifacts found in dist directory.")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"PyInstaller failed with return code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)

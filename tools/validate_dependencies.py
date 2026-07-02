"""Validate installed packages against a requirements file.

Used by the build scripts and tests to detect missing, outdated, or
unpinned dependencies before packaging. Exits nonzero from the CLI when
missing or outdated packages are found; unpinned entries are warnings.
"""

import argparse
import importlib.metadata
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("validate_dependencies")

# Requirement-file lines that are not package specs.
_SKIP_PREFIXES = ("#", "-", "--")


def parse_requirements(path: str) -> dict:
    """Parse a requirements file into ``{name: version_spec}``.

    ``version_spec`` is the raw spec string (e.g. ``"==1.25.2"`` or
    ``">=3.8"``); an empty string means no version constraint.
    """
    requirements: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.split("#", 1)[0].strip()
            if not line or line.startswith(_SKIP_PREFIXES):
                continue
            # Strip environment markers and extras: "pkg[extra]==1.0; marker"
            line = line.split(";", 1)[0].strip()
            for idx, char in enumerate(line):
                if char in "=<>!~":
                    name = line[:idx].strip()
                    spec = line[idx:].strip()
                    break
            else:
                name, spec = line, ""
            name = name.split("[", 1)[0].strip()
            if name:
                requirements[name] = spec
    return requirements


def _installed_versions() -> dict:
    """Return ``{lowercase_name: version}`` for installed distributions."""
    installed: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        if name:
            installed[name.lower()] = dist.version
    return installed


def check_dependencies(path: str):
    """Compare requirements in ``path`` with the installed environment.

    Returns:
        Tuple of (missing, outdated, unpinned) where missing/unpinned are
        lists of package names and outdated is a list of
        ``(name, required, installed)`` tuples.
    """
    requirements = parse_requirements(path)
    installed = _installed_versions()

    missing = []
    outdated = []
    unpinned = []

    for name, spec in requirements.items():
        key = name.lower()
        if key not in installed:
            missing.append(name)
            logger.warning("Missing dependency: %s%s", name, spec)
            continue
        if not spec.startswith("=="):
            unpinned.append(name)
            logger.info("Unpinned dependency: %s%s", name, spec)
            continue
        required_version = spec[2:].strip()
        if installed[key] != required_version:
            outdated.append((name, required_version, installed[key]))
            logger.warning(
                "Version mismatch for %s: required %s, installed %s",
                name,
                required_version,
                installed[key],
            )

    return missing, outdated, unpinned


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "requirements",
        nargs="?",
        default="requirements.txt",
        help="Path to the requirements file (default: requirements.txt)",
    )
    parser.add_argument(
        "--strict-unpinned",
        action="store_true",
        help="Also fail when unpinned dependencies are present",
    )
    args = parser.parse_args(argv)

    missing, outdated, unpinned = check_dependencies(args.requirements)

    logger.info(
        "Dependency check: %d missing, %d outdated, %d unpinned",
        len(missing),
        len(outdated),
        len(unpinned),
    )

    if missing or outdated:
        return 1
    if unpinned and args.strict_unpinned:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

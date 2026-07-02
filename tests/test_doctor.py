"""Smoke tests for the rf-mapper-doctor health check."""

from sim_rf_map import doctor


def test_doctor_runs_healthy(capsys):
    exit_code = doctor.main([])
    out = capsys.readouterr().out
    assert "RF Mapper doctor" in out
    assert "Optional features:" in out
    # The dev environment installs all core deps, so doctor reports healthy.
    assert exit_code == 0
    assert "Core installation is healthy." in out


def test_doctor_reports_core_modules(capsys):
    doctor.main([])
    out = capsys.readouterr().out
    for module in ("numpy", "matplotlib", "PIL", "skimage", "psutil"):
        assert f"core dependency: {module}" in out

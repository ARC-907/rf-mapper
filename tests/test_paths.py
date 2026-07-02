from pathlib import Path

from sim_rf_map import paths


def test_package_and_project_root_are_absolute():
    assert paths.PACKAGE_ROOT.is_absolute()
    assert paths.PROJECT_ROOT.is_absolute()
    assert paths.PACKAGE_ROOT.name == "sim_rf_map"


def test_get_base_dir_source_mode():
    # Not frozen in the test environment -> base dir is the project root.
    assert paths.get_base_dir() == paths.PROJECT_ROOT


def test_get_base_dir_frozen_mode(monkeypatch, tmp_path):
    fake_exe = tmp_path / "rf_mapper.exe"
    fake_exe.write_text("")
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", str(fake_exe))
    assert paths.get_base_dir() == tmp_path


def test_writable_dirs_created_and_absolute(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path))
    for func, name in [
        (paths.get_outputs_dir, "outputs"),
        (paths.get_logs_dir, "logs"),
        (paths.get_reports_dir, "reports"),
        (paths.get_uploads_dir, "uploads"),
        (paths.get_sessions_dir, "sessions"),
    ]:
        result = func()
        assert result.is_absolute()
        assert result.exists()
        assert result.is_dir()
        assert result == tmp_path / name


def test_rf_mapper_data_dir_env_override_read_at_call_time(tmp_path, monkeypatch):
    # No override -> base dir is the (non-frozen) project root.
    monkeypatch.delenv(paths.DATA_DIR_ENV_VAR, raising=False)
    default_outputs = paths.get_outputs_dir()
    assert default_outputs == paths.PROJECT_ROOT / "outputs"

    # Set override -> subsequent calls immediately honor it, no reload needed.
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path))
    overridden_outputs = paths.get_outputs_dir()
    assert overridden_outputs == tmp_path / "outputs"
    assert overridden_outputs.exists()

    # Unset again -> reverts back without reloading the module.
    monkeypatch.delenv(paths.DATA_DIR_ENV_VAR, raising=False)
    assert paths.get_outputs_dir() == paths.PROJECT_ROOT / "outputs"


def test_weights_dir_not_affected_by_data_dir_override(tmp_path, monkeypatch):
    monkeypatch.setenv(paths.DATA_DIR_ENV_VAR, str(tmp_path))
    weights_dir = paths.get_weights_dir()
    assert weights_dir == paths.get_base_dir() / "weights"
    assert weights_dir.exists()


def test_field_dir_not_auto_created(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", str(tmp_path / "app.exe"))
    field_dir = paths.get_field_dir()
    assert field_dir == tmp_path / "field"
    assert not field_dir.exists()


def test_user_config_dir_and_default_config_path(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    user_dir = paths.get_user_config_dir()
    assert user_dir == tmp_path / ".sim_rf_map"
    assert user_dir.exists()

    config_path = paths.get_default_config_path()
    assert config_path == user_dir / "config.json"

from core import config


def test_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "config.ini"))
    assert config.load_config() == config.DEFAULTS


def test_save_merges(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "config.ini"))
    config.save_config(language="en")
    config.save_config(structure="antenna")
    cfg = config.load_config()
    assert cfg["language"] == "en"
    assert cfg["structure"] == "antenna"
    assert cfg["api_server_exe"] == config.DEFAULTS["api_server_exe"]


def test_corrupted_file(tmp_path, monkeypatch):
    path = tmp_path / "config.ini"
    path.write_text("pas un ini", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_FILE", str(path))
    assert config.load_config() == config.DEFAULTS

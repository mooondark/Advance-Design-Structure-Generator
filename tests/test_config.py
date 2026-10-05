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


KEYS = ["steel_frame", "antenna", "concrete_frame"]


def _cfg(tmp_path, monkeypatch, text=None):
    path = tmp_path / "config.ini"
    if text is not None:
        path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_FILE", str(path))
    return path


def test_view_keys_created_and_all_visible(tmp_path, monkeypatch):
    path = _cfg(tmp_path, monkeypatch)
    assert config.visible_structures(KEYS) == KEYS
    text = path.read_text(encoding="utf-8")
    for name in ("View_SteelFrame", "View_Antenna", "View_ConcreteFrame"):
        assert f"{name} = True" in text


def test_hide_with_false_or_zero(tmp_path, monkeypatch):
    path = _cfg(tmp_path, monkeypatch, "[General]\nView_Antenna = false\nView_ConcreteFrame = 0\n")
    assert config.visible_structures(KEYS) == ["steel_frame"]
    assert "View_SteelFrame = True" in path.read_text(encoding="utf-8")


def test_view_keys_case_insensitive_and_invalid_means_visible(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch, "[General]\nview_steelframe = FALSE\nView_Antenna = peut-etre\n")
    assert config.visible_structures(KEYS) == ["antenna", "concrete_frame"]


def test_all_hidden_shows_everything(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch, "[General]\nView_SteelFrame = 0\nView_Antenna = 0\nView_ConcreteFrame = 0\n")
    assert config.visible_structures(KEYS) == KEYS


def test_existing_view_values_not_overwritten(tmp_path, monkeypatch):
    path = _cfg(tmp_path, monkeypatch, "[General]\nView_Antenna = 0\n")
    config.visible_structures(KEYS)
    config.visible_structures(KEYS)
    assert "View_Antenna = 0" in path.read_text(encoding="utf-8")


def test_save_config_keeps_view_keys(tmp_path, monkeypatch):
    path = _cfg(tmp_path, monkeypatch, "[General]\nView_Antenna = False\n")
    config.save_config(language="en")
    text = path.read_text(encoding="utf-8")
    assert "View_Antenna = False" in text and "language = en" in text
    assert config.visible_structures(KEYS) == ["steel_frame", "concrete_frame"]


DEFAULT_HIDDEN = {"convoyeur": False}
ALL = KEYS + ["convoyeur"]


def test_default_false_creates_hidden_key(tmp_path, monkeypatch):
    path = _cfg(tmp_path, monkeypatch)
    assert config.visible_structures(ALL, DEFAULT_HIDDEN) == KEYS
    text = path.read_text(encoding="utf-8")
    assert "View_Convoyeur = False" in text and "View_SteelFrame = True" in text


def test_default_false_can_be_enabled(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch, "[General]\nView_Convoyeur = True\n")
    assert config.visible_structures(ALL, DEFAULT_HIDDEN) == ALL


def test_invalid_value_uses_structure_default(tmp_path, monkeypatch):
    _cfg(tmp_path, monkeypatch, "[General]\nView_Convoyeur = peut-etre\nView_Antenna = peut-etre\n")
    assert config.visible_structures(ALL, DEFAULT_HIDDEN) == ["steel_frame", "antenna", "concrete_frame"]


def test_only_missing_key_added_to_existing_config(tmp_path, monkeypatch):
    path = _cfg(tmp_path, monkeypatch,
                "[General]\nlanguage = pl\nstructure = antenna\nView_SteelFrame = 0\nView_Antenna = 1\n"
                "View_ConcreteFrame = True\n")
    assert config.visible_structures(ALL, DEFAULT_HIDDEN) == ["antenna", "concrete_frame"]
    text = path.read_text(encoding="utf-8")
    assert "language = pl" in text and "View_SteelFrame = 0" in text and "View_Antenna = 1" in text
    assert "View_Convoyeur = False" in text


def test_save_config_keeps_hidden_default_key(tmp_path, monkeypatch):
    path = _cfg(tmp_path, monkeypatch)
    config.visible_structures(ALL, DEFAULT_HIDDEN)
    config.save_config(language="es")
    assert "View_Convoyeur = False" in path.read_text(encoding="utf-8")

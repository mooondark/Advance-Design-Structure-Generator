import pytest

from core import param_sections
from core.concrete import parse_section
from core.profiles import PROFILES
from structures import STRUCTURES

CONTRACT = ["KEY", "TITLE_KEY", "ICON", "MATERIALS", "DEFAULT_MATERIAL", "ELEMENTS", "DEFAULTS",
            "render_form", "preview", "validate", "build"]


def test_fallback_structure_is_first():
    # La premiere structure du registre sert de repli (config.ini inconnu).
    assert next(iter(STRUCTURES)) == "steel_frame"


@pytest.mark.parametrize("key", list(STRUCTURES))
def test_contract(key):
    s = STRUCTURES[key]
    for attr in CONTRACT:
        assert hasattr(s, attr), f"{key}.{attr} manquant"
    assert s.KEY == key
    assert s.DEFAULT_MATERIAL in s.MATERIALS
    assert not set(s.ELEMENTS) & set(s.DEFAULTS)
    assert "M" not in s.DEFAULTS
    for name, (label_key, families, default) in s.ELEMENTS.items():
        if families == "beton":
            parse_section(default)
            continue
        assert all(f in PROFILES or f in param_sections.FAMILIES for f in families),             f"{key}.{name} : famille inconnue"
        parsed = param_sections.parse(default)
        assert (parsed and parsed[0] in families) or any(default in PROFILES.get(f, ()) for f in families),             f"{key}.{name} : {default} hors familles"


@pytest.mark.parametrize("key", list(STRUCTURES))
def test_visible_by_default_is_bool(key):
    assert isinstance(getattr(STRUCTURES[key], "VISIBLE_BY_DEFAULT", True), bool)


def test_convoyeur_hidden_by_default():
    assert STRUCTURES["convoyeur"].VISIBLE_BY_DEFAULT is False
    assert all(getattr(s, "VISIBLE_BY_DEFAULT", True) for k, s in STRUCTURES.items() if k != "convoyeur")

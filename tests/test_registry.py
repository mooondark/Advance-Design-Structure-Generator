import pytest

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
        assert all(f in PROFILES for f in families), f"{key}.{name} : famille inconnue"
        assert any(default in PROFILES[f] for f in families), f"{key}.{name} : {default} hors familles"

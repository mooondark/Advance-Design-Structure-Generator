import pytest

from core.ad_api import MATERIALS
from core.profiles import PROFILES
from structures import STRUCTURES

CONTRACT = ["KEY", "TITLE_KEY", "ICON", "DEFAULT_MATERIAL", "ELEMENTS", "DEFAULTS",
            "render_form", "preview", "validate", "build"]


def test_order():
    assert list(STRUCTURES) == ["steel_frame", "antenna"]


@pytest.mark.parametrize("key", ["steel_frame", "antenna"])
def test_contract(key):
    s = STRUCTURES[key]
    for attr in CONTRACT:
        assert hasattr(s, attr), f"{key}.{attr} manquant"
    assert s.KEY == key
    assert s.DEFAULT_MATERIAL in MATERIALS
    assert not set(s.ELEMENTS) & set(s.DEFAULTS)
    assert "M" not in s.DEFAULTS
    for name, (label_key, families, default) in s.ELEMENTS.items():
        assert all(f in PROFILES for f in families), f"{key}.{name} : famille inconnue"
        assert any(default in PROFILES[f] for f in families), f"{key}.{name} : {default} hors familles"

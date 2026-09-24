from core.profiles import PROFILES
from tools.gen_profiles import parse

SAMPLE = """# Titre

## Famille HEA

**Code famille :** HEA

| name | h | b |
|---|---|---|
| HEA100 | 96 | 100 |
| HEA120 | 114 | 120 |

## Famille HP (US)

| Name | h |
|---|---|
| HP8x36 | 204 |
"""


def test_parse_sample():
    assert parse(SAMPLE) == {"HEA": ["HEA100", "HEA120"], "HP (US)": ["HP8x36"]}


def test_generated_module():
    assert len(PROFILES) == 35
    assert "HEA400" in PROFILES["HEA"]
    assert "CHS88.9x3C" in PROFILES["CHSC"]
    assert all(PROFILES.values())
    assert not any(n.lower() == "name" for names in PROFILES.values() for n in names)

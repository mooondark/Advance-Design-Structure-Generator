import configparser
import os
import re

import pytest

from core.i18n import LANG_FILES
from structures import STRUCTURES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Le code commun (app.py, core/) doit trouver ses cles dans [common] quelle que soit la structure active.
SOURCES = {"common": ["app.py", "core/ui.py", "core/runner.py"],
           **{key: [f"structures/{key}.py"] for key in STRUCTURES}}
# Cles construites dynamiquement (format_func) : non detectees par la recherche de T("...").
DYNAMIC = {
    "common": {"shape_C", "shape_R", "shape_D", "dim_C", "dim_D"},
    "steel_frame": {"appui_hinged", "appui_fixed"},
    "antenna": {"base_triangle", "base_square"},
    "concrete_frame": {"appui_hinged", "appui_fixed"},
}
EXTRA = {scope: DYNAMIC.get(scope, set()) | (
    {label for label, _fam, _default in STRUCTURES[scope].ELEMENTS.values()} if scope in STRUCTURES else set())
    for scope in SOURCES}


def _keys(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return set(re.findall(r'T\(\s*["\']([A-Za-z_]+)["\']', f.read()))


def _read(code):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(os.path.join(ROOT, "lang", LANG_FILES[code]), encoding="utf-8")
    return parser


@pytest.mark.parametrize("code", list(LANG_FILES))
def test_structure_titles_in_common(code):
    # Le selecteur affiche tous les titres quelle que soit la structure active.
    parser = _read(code)
    for key, s in STRUCTURES.items():
        assert parser.has_option("common", s.TITLE_KEY), f"{code}: [common] {s.TITLE_KEY} absente ({key})"


@pytest.mark.parametrize("code", list(LANG_FILES))
def test_placeholders_match_french(code):
    fr, other = _read("fr"), _read(code)
    for section in fr.sections():
        for key, value in fr[section].items():
            if other.has_option(section, key):
                assert set(re.findall(r"\{(\w+)", value)) == set(re.findall(r"\{(\w+)", other[section][key])), \
                    f"{code}: [{section}] {key} parametres differents"


@pytest.mark.parametrize("code", list(LANG_FILES))
def test_used_keys_translated_in_scope(code):
    parser = _read(code)
    for scope, files in SOURCES.items():
        keys = EXTRA[scope].union(*(_keys(rel) for rel in files))
        for key in keys:
            assert parser.has_option(scope, key) or parser.has_option("common", key), \
                f"{code}: [{scope}] {key} absente"


@pytest.mark.parametrize("code, word", [("fr", "béton"), ("en", "oncrete"), ("pl", "beton"),
                                        ("es", "hormigón"), ("pt", "betão")])
def test_concrete_material_label(code, word):
    # [common] ui_materiau parle d'acier : le Portique beton le redefinit dans sa section.
    assert word in _read(code).get("concrete_frame", "ui_materiau", fallback="")

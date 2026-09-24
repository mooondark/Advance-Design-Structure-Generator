import configparser
import os
import re

import pytest

from core.i18n import LANG_FILES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Le code commun (app.py, core/) doit trouver ses cles dans [common] quelle que soit la structure active.
SOURCES = {
    "common": ["app.py", "core/ui.py", "core/runner.py"],
    "steel_frame": ["structures/steel_frame.py"],
    "antenna": ["structures/antenna.py"],
}
# Cles non appelees par T("...") litteral : TITLE_KEY, libelles de ELEMENTS, format_func dynamiques.
EXTRA = {
    "common": {"structure_steel_frame", "structure_antenna"},
    "steel_frame": {"ui_sec_poteaux", "ui_sec_arbaletriers", "ui_sec_pannes", "appui_hinged", "appui_fixed"},
    "antenna": {"ui_section", "ui_section_guy", "base_triangle", "base_square"},
}


def _keys(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return set(re.findall(r'T\(\s*["\']([A-Za-z_]+)["\']', f.read()))


@pytest.mark.parametrize("code", list(LANG_FILES))
def test_used_keys_translated_in_scope(code):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(os.path.join(ROOT, "lang", LANG_FILES[code]), encoding="utf-8")
    for scope, files in SOURCES.items():
        keys = EXTRA[scope].union(*(_keys(rel) for rel in files))
        for key in keys:
            assert parser.has_option(scope, key) or parser.has_option("common", key), \
                f"{code}: [{scope}] {key} absente"

import configparser
import os

from core.config import get_app_dir

DEFAULT_LANG = "fr"
LANG_FILES = {"fr": "fr.ini", "en": "en.ini", "pl": "pl.ini"}
LANG_LABELS = {"fr": "Français", "en": "English", "pl": "Polski"}

_parser = configparser.ConfigParser(interpolation=None)
_scope = "common"


def load_language(code, lang_dir=None):
    global _parser
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    path = os.path.join(lang_dir or os.path.join(get_app_dir(), "lang"),
                        LANG_FILES.get(code, LANG_FILES[DEFAULT_LANG]))
    parser.read(path, encoding="utf-8")
    _parser = parser


def set_scope(name):
    global _scope
    _scope = name


def T(key, **kw):
    for section in (_scope, "common"):
        if _parser.has_option(section, key):
            value = _parser.get(section, key).replace("\n", "\n")
            return value.format(**kw) if kw else value
    return f"[{key}]"

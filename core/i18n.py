import configparser
import os
import threading

from core.config import get_app_dir

DEFAULT_LANG = "fr"
LANG_FILES = {"fr": "fr.ini", "en": "en.ini", "pl": "pl.ini"}
LANG_LABELS = {"fr": "Français", "en": "English", "pl": "Polski"}

# Etat par thread : Streamlit execute chaque session dans son propre thread.
_state = threading.local()


def load_language(code, lang_dir=None):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    path = os.path.join(lang_dir or os.path.join(get_app_dir(), "lang"),
                        LANG_FILES.get(code, LANG_FILES[DEFAULT_LANG]))
    parser.read(path, encoding="utf-8")
    _state.parser = parser


def set_scope(name):
    _state.scope = name


def T(key, **kw):
    parser = getattr(_state, "parser", None)
    if parser is None:
        return f"[{key}]"
    for section in (getattr(_state, "scope", "common"), "common"):
        if parser.has_option(section, key):
            value = parser.get(section, key).replace("\\n", "\n")
            try:
                return value.format(**kw) if kw else value
            except (KeyError, IndexError):
                # Traduction avec un {parametre} inconnu : texte brut plutot qu'un plantage.
                return value
    return f"[{key}]"

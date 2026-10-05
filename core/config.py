import configparser
import os
import sys

DEFAULTS = {
    "language": "fr",
    "api_server_exe": r"C:\Program Files\Graitec\Advance Design\2027\Bin\AD.API.Srv.exe",
    "structure": "steel_frame",
}


def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_FILE = os.path.join(get_app_dir(), "config.ini")


def _read_raw():
    """Section [General] telle quelle (casse des cles conservee) ; {} si fichier absent ou illisible."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    try:
        parser.read(CONFIG_FILE, encoding="utf-8")
    except configparser.Error:
        return {}
    return dict(parser["General"]) if parser.has_section("General") else {}


def _write_raw(raw):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser["General"] = raw
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            parser.write(f)
    except OSError:
        pass


def _get(raw, key, default=None):
    """Lecture insensible a la casse."""
    for k, v in raw.items():
        if k.lower() == key.lower():
            return v
    return default


def _set(raw, key, value):
    for k in list(raw):
        if k.lower() == key.lower():
            raw[k] = value
            return
    raw[key] = value


def load_config():
    raw = _read_raw()
    return {k: _get(raw, k, v) for k, v in DEFAULTS.items()}


def save_config(**values):
    raw = _read_raw()
    for k, v in {**load_config(), **values}.items():
        _set(raw, k, v)
    _write_raw(raw)


def view_key(structure_key):
    """'steel_frame' -> 'View_SteelFrame'."""
    return "View_" + "".join(w.capitalize() for w in structure_key.split("_"))


def visible_structures(structure_keys, defaults=None):
    """Structures a afficher d'apres les cles View_<Nom> de config.ini (true/false, 1/0...).
    defaults : {cle: bool} valeur par defaut par structure (True si absente).
    Cle absente : creee avec le defaut de la structure ; valeur illisible : defaut de la structure ;
    tout masque : tout est affiche."""
    defaults = defaults or {}
    raw = _read_raw()
    created = False
    visible = []
    for key in structure_keys:
        default = defaults.get(key, True)
        name = view_key(key)
        value = _get(raw, name)
        if value is None:
            raw[name] = value = str(default)
            created = True
        if configparser.RawConfigParser.BOOLEAN_STATES.get(value.strip().lower(), default):
            visible.append(key)
    if created:
        _write_raw(raw)
    return visible or list(structure_keys)

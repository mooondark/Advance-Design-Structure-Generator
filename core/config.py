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


def load_config():
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(CONFIG_FILE, encoding="utf-8")
    except configparser.Error:
        return dict(DEFAULTS)
    section = parser["General"] if parser.has_section("General") else {}
    return {k: section.get(k, v) for k, v in DEFAULTS.items()}


def save_config(**values):
    cfg = load_config()
    cfg.update(values)
    parser = configparser.ConfigParser(interpolation=None)
    parser["General"] = cfg
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            parser.write(f)
    except OSError:
        pass

"""Sections acier parametriques AD : I<h>*<tw>+<b>*<tf> et U<h>*<tw>+<b>*<tf> (cm)."""
import re

FAMILIES = {"I*": "I", "U*": "U", "CS2": "I"}   # CS2 : deux sections I identiques
DEFAULT_DIMS = [20.0, 1.0, 10.0, 1.0]
_NUM = r"(\d+(?:\.\d+)?)"
_RE = re.compile(rf"^([IU]){_NUM}\*{_NUM}\+{_NUM}\*{_NUM}$")


def parse(name):
    s = str(name).strip()
    if s.startswith("CS2 "):
        halves = s[4:].split()
        one = parse(halves[0]) if len(halves) == 2 and halves[0] == halves[1] else None
        return ("CS2", one[1]) if one and one[0] == "I*" else None
    m = _RE.match(str(name).strip())
    if not m:
        return None
    return m.group(1) + "*", [float(x) for x in m.groups()[1:]]


def name(family, dims):
    h, tw, b, tf = dims
    one = f"{FAMILIES[family]}{h:g}*{tw:g}+{b:g}*{tf:g}"
    return f"CS2 {one} {one}" if family == "CS2" else one

"""Sections beton parametriques : C<cote>, R<b>*<h>, D<diametre> (cm entiers)."""

SHAPES = {"C": 1, "R": 2, "D": 1}


def section_name(shape, dims):
    return shape + "*".join(str(int(d)) for d in dims)


def parse_section(name):
    text = "".join(str(name).split())
    shape, rest = text[:1], text[1:]
    if shape not in SHAPES:
        raise ValueError(f"forme inconnue : {name!r}")
    parts = rest.split("*")
    if len(parts) != SHAPES[shape] or not all(p.isdigit() and int(p) > 0 for p in parts):
        raise ValueError(f"dimensions invalides : {name!r}")
    return shape, [int(p) for p in parts]


def section_height(name):
    _shape, dims = parse_section(name)
    return dims[-1] / 100

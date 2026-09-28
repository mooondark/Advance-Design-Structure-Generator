import pytest

from core.concrete import SHAPES, parse_section, section_height, section_name


def test_shapes():
    assert SHAPES == {"C": 1, "R": 2, "D": 1}


@pytest.mark.parametrize("shape, dims, name", [("C", [30], "C30"), ("R", [20, 50], "R20*50"), ("D", [40], "D40")])
def test_name_round_trip(shape, dims, name):
    assert section_name(shape, dims) == name
    assert parse_section(name) == (shape, dims)


def test_parse_strips_spaces():
    assert parse_section(" R 20 * 50 ") == ("R", [20, 50])


@pytest.mark.parametrize("name", ["", "X30", "C", "R20", "C30*40", "R20*0", "Cabc", "R20*50*60", "C-5", "C2.5"])
def test_parse_invalid(name):
    with pytest.raises(ValueError):
        parse_section(name)


@pytest.mark.parametrize("name, h", [("C30", 0.30), ("R20*50", 0.50), ("D25", 0.25)])
def test_height(name, h):
    assert section_height(name) == pytest.approx(h)

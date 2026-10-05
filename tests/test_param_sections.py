import pytest

from core import param_sections as ps


def test_parse_i():
    assert ps.parse("I68*1+18*0.5") == ("I*", [68.0, 1.0, 18.0, 0.5])


def test_parse_u_decimals():
    assert ps.parse("U12*0.55+5.3*0.8") == ("U*", [12.0, 0.55, 5.3, 0.8])


def test_parse_cs2():
    assert ps.parse("CS2 I17.5*0.8+9*0.5 I17.5*0.8+9*0.5") == ("CS2", [17.5, 0.8, 9.0, 0.5])


def test_cs2_name_applies_section_twice():
    assert ps.name("CS2", [17.5, 1.1, 17.5, 0.75]) == "CS2 I17.5*1.1+17.5*0.75 I17.5*1.1+17.5*0.75"


def test_parse_cs2_different_halves_none():
    assert ps.parse("CS2 I17.5*0.8+9*0.5 I68*1+18*0.5") is None


@pytest.mark.parametrize("n", ["HEA200", "CHS42.4x4C", "I68*1", ""])
def test_parse_none(n):
    assert ps.parse(n) is None


@pytest.mark.parametrize("n", ["I68*1+18*0.5", "U12*0.55+5.3*0.8", "I17.5*1.1+17.5*0.75"])
def test_roundtrip(n):
    fam, dims = ps.parse(n)
    assert ps.name(fam, dims) == n

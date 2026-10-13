import pytest

from core.util import lines3d, parse_floats


def test_parse_floats():
    assert parse_floats("20, 40,") == [20.0, 40.0]
    assert parse_floats("") == [] and parse_floats(None) == []
    with pytest.raises(ValueError):
        parse_floats("20;40")


def test_lines3d_breaks_between_segments():
    trace = lines3d([((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (0, 1, 2))], "#4A7FE0", 3)
    assert list(trace.x) == [0, 1, None, 0, 0, None]
    assert list(trace.z) == [0, 0, None, 0, 2, None]
    assert trace.mode == "lines" and trace.line.width == 3

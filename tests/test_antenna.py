import pytest

from core import ad_api
from structures import antenna
from structures.antenna import generate_antenna_tower


def _p(**kw):
    p = {"height": 40.0, "base_type": "square", "num_levels": 40, "base_size": 0.6,
         "guy_levels": 2, "guy_heights": "20,40", "anchor_distance": 20.0,
         "creer_systemes": False, "section": "CHS88.9x3C", "section_guy": "CHS21.3x2C", "M": "S235"}
    p.update(kw)
    return p


def test_triangle_no_guys():
    m = generate_antenna_tower(20, "triangle", 20, 0.5)["metadata"]
    assert m["total_nodes"] == 63
    assert m["total_elements"] == 180
    assert m["total_supports"] == 3
    assert m["total_guy_wires"] == 0
    assert m["total_anchors"] == 0


def test_square_with_guys():
    p = generate_antenna_tower(40, "square", 40, 0.6, guy_levels=2, guy_heights=[20, 40], anchor_distance=20)
    m = p["metadata"]
    assert m["total_elements"] == 480
    assert m["total_supports"] == 4
    assert m["total_guy_wires"] == 8
    assert m["total_anchors"] == 4


def test_build_counts(monkeypatch):
    calls = {"lin": 0, "sup": 0, "sec": 0}
    monkeypatch.setattr(ad_api, "create_material", lambda *a, **k: 1)
    monkeypatch.setattr(ad_api, "create_system", lambda *a, **k: 9)

    def count(name):
        def f(*a, **k):
            calls[name] += 1
            return 2
        return f

    monkeypatch.setattr(ad_api, "create_section", count("sec"))
    monkeypatch.setattr(ad_api, "create_linear_element", count("lin"))
    monkeypatch.setattr(ad_api, "create_support", count("sup"))

    rows = antenna.build("http://h", _p(), lambda m: None)

    assert calls == {"lin": 480 + 8, "sup": 4 + 4, "sec": 2}
    assert rows[-1][1] == 480 + 8 + 4 + 4


@pytest.mark.parametrize("text", ["abc", "20;40", "20,,x"])
def test_bad_guy_heights_is_validation_error(text):
    with pytest.raises(ValueError, match="ui_guy_heights_invalid"):
        antenna.validate(_p(guy_heights=text))


def test_guy_heights_order_and_count():
    with pytest.raises(ValueError, match="val_guy_order"):
        antenna.validate(_p(guy_heights="40,20"))
    with pytest.raises(ValueError, match="val_guy_count"):
        antenna.validate(_p(guy_heights="20"))


def test_preview_bad_heights_raises():
    with pytest.raises(ValueError):
        antenna.preview(_p(guy_heights="abc"))


def test_preview_ok():
    fig = antenna.preview(_p())
    assert len(fig.data) == 3

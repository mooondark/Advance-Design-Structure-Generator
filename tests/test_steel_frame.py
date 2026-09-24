import pytest

from core import ad_api
from structures import steel_frame


def _p(**kw):
    p = {"n": 5, "e": 5.0, "Hg": 6.0, "Hd": 4.0, "L": 18.0, "AR": 7.0, "F": 1.2,
         "TypeAppui": "HINGED", "Npg": 5, "Npd": 7, "Dbg": 0.3, "Dbd": 0.3,
         "creer_parois": True, "creer_systemes": False,
         "Sp": "HEA400", "Sa": "IPE400", "Sn": "IPE160", "M": "S275"}
    p.update(kw)
    return p


def test_build_counts(monkeypatch):
    calls = {"lin": 0, "sup": 0, "sec": 0, "area": 0}
    monkeypatch.setattr(ad_api, "create_material", lambda *a, **k: 1)
    monkeypatch.setattr(ad_api, "create_system", lambda *a, **k: 9)
    monkeypatch.setattr(ad_api, "create_dead_load_case", lambda *a, **k: (3, 4))

    def count(name):
        def f(*a, **k):
            calls[name] += 1
            return 2
        return f

    monkeypatch.setattr(ad_api, "create_section", count("sec"))
    monkeypatch.setattr(ad_api, "create_linear_element", count("lin"))
    monkeypatch.setattr(ad_api, "create_support", count("sup"))
    monkeypatch.setattr(ad_api, "create_load_area", count("area"))

    rows = steel_frame.build("http://h", _p(), lambda m: None)

    # 5 portiques x 4 barres + 4 travees x (5 + 7) pannes
    assert calls == {"lin": 20 + 48, "sup": 10, "sec": 3, "area": 6}
    assert rows[-1][1] == 20 + 48 + 10 + 6


def test_validate_ok():
    steel_frame.validate(_p())


def test_validate_ar_outside_span():
    with pytest.raises(ValueError, match="val_AR"):
        steel_frame.validate(_p(AR=18.0))


def test_validate_purlin_offset_too_long():
    with pytest.raises(ValueError, match="val_Dbg_long"):
        steel_frame.validate(_p(Dbg=50.0))


def test_preview_segments():
    fig = steel_frame.preview(_p())
    assert len(fig.data) == 3

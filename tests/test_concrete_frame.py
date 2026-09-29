import itertools

import pytest

from core import ad_api
from structures import concrete_frame as cf


def _p(**kw):
    p = {"Nx": 2, "Ny": 4, "Lx": 5.0, "Ly": 5.0, "Ne": 2, "He": "3.0", "Ep": 0.20, "TypeAppui": "FIXED",
         "creer_systemes": True, "Spf": "C30", "Spi": "C20", "Sbr": "R20*50", "Sbi": "R20*70", "M": "C25/30"}
    p.update(kw)
    return p


@pytest.fixture
def api(monkeypatch):
    rec = {"systems": {}, "linear": [], "support": [], "planar": [], "levels": [], "order": []}
    ids = itertools.count(100)

    def create_system(host, name, parent_eid=0):
        eid = next(ids)
        rec["systems"][eid] = (name, parent_eid)
        rec["order"].append("system")
        return eid

    def create_linear_element(host, a, b, mat, sec, beam_type="beamWStandardBending", relaxation=None,
                              user_name=None, system_ids=None, excentration=None):
        rec["linear"].append({"a": a, "b": b, "sec": sec, "name": user_name, "sys": system_ids, "exc": excentration})
        return 1

    def create_support(host, pt, mat, type_appui, user_name=None, system_ids=None):
        rec["support"].append({"pt": pt, "type": type_appui, "sys": system_ids})
        return 1

    def create_planar_element(host, pts, mat, thickness, eccentricity, user_name=None, system_ids=None):
        rec["planar"].append({"pts": pts, "t": thickness, "e": eccentricity, "name": user_name, "sys": system_ids})
        return 1

    def update_system_level(host, eid, name, number, bottom, top):
        rec["levels"].append((eid, name, number, bottom, top))
        rec["order"].append("level")

    monkeypatch.setattr(ad_api, "create_material", lambda host, name: 1)
    monkeypatch.setattr(ad_api, "create_section", lambda host, name: name)
    monkeypatch.setattr(ad_api, "create_system", create_system)
    monkeypatch.setattr(ad_api, "create_linear_element", create_linear_element)
    monkeypatch.setattr(ad_api, "create_support", create_support)
    monkeypatch.setattr(ad_api, "create_planar_element", create_planar_element)
    monkeypatch.setattr(ad_api, "update_system_level", update_system_level)
    return rec


def _place(rec, sys_ids):
    sub, parent = rec["systems"][sys_ids[0]]
    return rec["systems"][parent][0], sub


def test_levels_and_heights():
    assert cf.levels(_p(He="3.0")) == [0.0, 3.0, 6.0]
    assert cf.levels(_p(He="3.5, 3")) == [0.0, 3.5, 6.5]


def test_counts(api):
    rows = cf.build("http://h", _p(), lambda m: None)
    cols = [l for l in api["linear"] if l["a"][2] != l["b"][2]]
    beams = [l for l in api["linear"] if l["a"][2] == l["b"][2]]
    assert len(cols) == 30 and sum(c["name"] == "Poteau façade" for c in cols) == 24
    assert sum(c["name"] == "Poteau intérieur" for c in cols) == 6
    assert len(beams) == 44 and sum(b["name"] == "Poutre de rive" for b in beams) == 24
    assert sum(b["name"] == "Poutre intérieure" for b in beams) == 20
    assert len(api["planar"]) == 2 and len(api["support"]) == 15
    assert {c["sec"] for c in cols if c["name"] == "Poteau façade"} == {"C30"}
    assert {b["sec"] for b in beams if b["name"] == "Poutre de rive"} == {"R20*50"}
    assert rows[-1][1] == 30 + 44 + 2 + 15


def test_beams_eccentric_columns_not(api):
    cf.build("http://h", _p(), lambda m: None)
    for l in api["linear"]:
        expected = cf.POUTRE_EXCENTRATION if l["a"][2] == l["b"][2] else None
        assert l["exc"] == expected


def test_elements_in_right_systems(api):
    # Un systeme par etage (Ne) : l'etage k contient ses poteaux (Z_(k-1) -> Z_k) et le plancher en tete (Z_k).
    cf.build("http://h", _p(), lambda m: None)
    z = [0.0, 3.0, 6.0]
    for l in api["linear"]:
        if l["a"][2] != l["b"][2]:
            k = z.index(l["b"][2])
            assert _place(api, l["sys"]) == (f"Étage {k} - R+{k - 1}", "POTEAU")
        else:
            k = z.index(l["a"][2])
            assert _place(api, l["sys"]) == (f"Étage {k} - R+{k - 1}", "POUTRE")
    for s in api["planar"]:
        k = z.index(s["pts"][0][2])
        assert _place(api, s["sys"]) == (f"Étage {k} - R+{k - 1}", "DALLE")
    for s in api["support"]:
        assert s["pt"][2] == 0.0 and _place(api, s["sys"]) == ("Étage 1 - R+0", "APPUI")
    roots = [name for name, parent in api["systems"].values() if parent == 0]
    assert roots == ["Étage 1 - R+0", "Étage 2 - R+1"]
    subs = sorted(name for name, parent in api["systems"].values() if parent != 0)
    assert subs.count("APPUI") == 1 and subs.count("VOILE") == 2


def test_levels_after_all_systems(api):
    cf.build("http://h", _p(), lambda m: None)
    assert api["order"].index("level") > max(i for i, o in enumerate(api["order"]) if o == "system")
    assert [(n, b, t) for _eid, _name, n, b, t in api["levels"]] == [(1, 0.0, 3.0), (2, 3.0, 6.0)]
    assert [name for _eid, name, *_ in api["levels"]] == ["Étage 1 - R+0", "Étage 2 - R+1"]


def test_slab_top_face_at_level(api):
    cf.build("http://h", _p(), lambda m: None)
    for s in api["planar"]:
        assert s["t"] == 0.20 and s["e"] == pytest.approx(cf.DALLE_EXCENTREMENT * 0.20)
        assert s["name"] == "Dalle"


def test_without_systems(api):
    cf.build("http://h", _p(creer_systemes=False), lambda m: None)
    assert api["systems"] == {} and api["levels"] == []
    assert all(l["sys"] is None for l in api["linear"] + api["support"] + api["planar"])


def test_validate_ok():
    cf.validate(_p())
    cf.validate(_p(He="3.5,3"))


@pytest.mark.parametrize("kw, key", [
    ({"He": "3,3,3"}, "val_he_count"),
    ({"He": "3,5", "Ne": 1}, "val_he_count"),
    ({"He": ""}, "val_he_count"),
    ({"He": "3,-1"}, "val_he"),
    ({"Nx": 0}, "val_nx"),
    ({"Ep": 0.0}, "val_ep"),
    ({"Sbi": "R20*400"}, "val_poutre_h"),
    ({"Ep": 0.6}, "val_ep_h"),
    ({"Spf": "X30"}, "val_section"),
])
def test_validate_errors(kw, key):
    with pytest.raises(ValueError, match=key):
        cf.validate(_p(**kw))


def test_validate_unreadable_heights():
    with pytest.raises(ValueError, match="ui_he_invalid"):
        cf.validate(_p(He="abc"))


def test_preview():
    assert len(cf.preview(_p()).data) == 4
    with pytest.raises(ValueError):
        cf.preview(_p(He="abc"))


def test_beam_eccentricity_verified_in_ad():
    # Verifie visuellement dans Advance Design : "centre_bas" place la poutre sous le plancher.
    assert cf.POUTRE_EXCENTRATION == "centre_bas"

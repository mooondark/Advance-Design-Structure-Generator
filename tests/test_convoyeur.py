import pytest

from core import ad_api
from structures import convoyeur


def _p(**kw):
    p = {**convoyeur.DEFAULTS, **{k: v[2] for k, v in convoyeur.ELEMENTS.items()}, "M": "S275"}
    p.update(kw)
    return p


def _mock(monkeypatch):
    calls = {"lin": [], "sup": 0, "sec": [], "sys": [], "mat": []}
    monkeypatch.setattr(ad_api, "create_material", lambda h, n: calls["mat"].append(n) or 1)
    monkeypatch.setattr(ad_api, "create_section", lambda h, n: calls["sec"].append(n) or 2)

    def lin(h, a, b, m, s, beam_type="x", **k):
        calls["lin"].append((beam_type, k["user_name"], k["system_ids"]))
        return 3

    monkeypatch.setattr(ad_api, "create_linear_element", lin)
    monkeypatch.setattr(ad_api, "create_support", lambda *a, **k: calls.__setitem__("sup", calls["sup"] + 1) or 4)
    monkeypatch.setattr(ad_api, "create_system", lambda h, n, parent_eid=0: calls["sys"].append((n, parent_eid)) or len(calls["sys"]))
    return calls


def test_build_counts(monkeypatch):
    calls = _mock(monkeypatch)
    rows = convoyeur.build("http://h", _p(), lambda m: None)
    assert len(calls["lin"]) == 113
    assert sum(1 for t in calls["lin"] if t[0] == "rigid") == 32
    assert calls["sup"] == 6
    assert calls["mat"] == ["S275", "Rigid", "C25/30"]
    assert len(calls["sys"]) == 12 - 1          # arborescence du modele sans la racine "Structure"
    assert ("Travée 1", 5) in calls["sys"]      # fils de "Convoyeur" (5e systeme cree)
    assert len(calls["sec"]) == len(set(calls["sec"]))   # chaque section creee une seule fois
    assert rows[-1][1] == 113 + 6


def test_validate_defaults_ok():
    convoyeur.validate(_p())


@pytest.mark.parametrize("kw, key", [
    (dict(pente=0), "val_conv_pos"),
    (dict(debord=0), "val_conv_pos"),
    (dict(L1=-1), "val_conv_pos"),
    (dict(n1=1, n2=1), "val_conv_n"),
    (dict(ntr=0), "val_conv_n"),
    (dict(n1=4, n2=4, ntr=4), "val_conv_n"),
    (dict(Ne2=0), "val_conv_n"),
    (dict(Hs3=5.0), "val_conv_hs3"),
])
def test_validate_rejects(kw, key):
    with pytest.raises(ValueError, match=key):
        convoyeur.validate(_p(**kw))


def test_preview_traces():
    assert len(convoyeur.preview(_p()).data) == 3

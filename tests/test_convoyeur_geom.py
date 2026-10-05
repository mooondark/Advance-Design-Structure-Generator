import json
import math
import os

import pytest

from structures.convoyeur_geom import build_model

REF = os.path.join(os.path.dirname(__file__), "data", "convoyeur_ref.json")
X_SHIFT = 0.087   # le modele d'origine place le sommet du portique 1 a X = 0.087


def _p(**kw):
    p = dict(pente=27.55, Em=1.16, debord=0.81, L1=5.6882, L2=8.5322, Ldeb=1.582,
             n1=4, n2=6, ntr=4, H1=0.4168, Hs3=1.293, Ne2=2, Ne3=3,
             E1=1.16, E2=1.5, E3=2.005,
             Sc="CHS42.4x4C", Sd="CHS60.3x4C", St="U12*0.55+5.3*0.8", Sm="I68*1+18*0.5",
             S1="I17.5*1.1+17.5*0.75", S2="I17.5*0.8+9*0.5",
             S31="CS2 I17.5*0.8+9*0.5 I17.5*0.8+9*0.5", S32="I17.5*0.8+9*0.5",
             Sx="SHS60x4C", Sdb="I68*1+18*0.5", Sdu="UPN220")
    p.update(kw)
    return p


def _close(a, b):
    # Tolerance Y plus large : le portique 3 du modele est dissymetrique, le generateur le symetrise.
    return abs(a[0] - b[0] + X_SHIFT) < 0.02 and abs(a[1] - b[1]) < 0.15 and abs(a[2] - b[2]) < 0.03


def test_default_counts():
    bars, supports = build_model(_p())
    assert len(bars) == 113
    assert sum(1 for b in bars if b[3] == "rigid") == 32
    assert len(supports) == 6


def test_default_matches_reference():
    ref = json.load(open(REF, encoding="utf-8"))
    bars, supports = build_model(_p())
    used = set()
    for r in ref["bars"]:
        for i, b in enumerate(bars):
            if i in used or b[:3] != (r["system"], r["name"], r["section"]):
                continue
            if (_close(b[4], r["a"]) and _close(b[5], r["b"])) or (_close(b[4], r["b"]) and _close(b[5], r["a"])):
                used.add(i)
                break
        else:
            pytest.fail(f"barre de reference absente : {r}")
    assert len(used) == 113
    for r in ref["supports"]:
        assert any(s[0] == r["system"] and _close(s[1], r["pt"]) for s in supports), r


@pytest.mark.parametrize("kw, n", [
    (dict(n1=6, n2=8), 129),
    (dict(n1=1, n2=2, ntr=1), 84),
    (dict(Ne2=1, Ne3=1), 104),
])
def test_counts_follow_parameters(kw, n):
    assert len(build_model(_p(**kw))[0]) == n


@pytest.mark.parametrize("kw", [dict(pente=1), dict(pente=100), dict(ntr=1), dict(Ne2=1, Ne3=1),
                                dict(n1=1, n2=2, ntr=1), dict(E2=3.0, E3=4.0)])
def test_no_degenerate_bar(kw):
    for b in build_model(_p(**kw))[0]:
        assert math.dist(b[4], b[5]) > 1e-3, b


def test_slope_applies_to_main_beams():
    bars, _ = build_model(_p(pente=10))
    b = next(b for b in bars if b[1] == "Poutre principale" and b[0] == "Travée 1")
    assert (b[5][2] - b[4][2]) / (b[5][0] - b[4][0]) == pytest.approx(0.10, abs=1e-6)


def test_end_template_follows_slope():
    bars, _ = build_model(_p(pente=10))
    o = next(b for b in bars if b[1] == "Poutre principale" and b[0] == "Travée 2" and b[5][1] == 0.0)[5]
    ref, _ = build_model(_p())
    o0 = next(b for b in ref if b[1] == "Poutre principale" and b[0] == "Travée 2" and b[5][1] == 0.0)[5]
    ends = [b for b in bars if b[0] == "Extrémité fin"]
    ends0 = [b for b in ref if b[0] == "Extrémité fin"]
    assert len(ends) == len(ends0) == 25
    for b, b0 in zip(ends, ends0):
        d, d0 = [math.dist(b[i], (o[0], b[i][1], o[2])) for i in (4, 5)], [math.dist(b0[i], (o0[0], b0[i][1], o0[2])) for i in (4, 5)]
        assert d == pytest.approx(d0, abs=1e-6)


def test_section_override_used():
    bars, _ = build_model(_p(Sc="CHS60.3x4C"))
    assert {b[2] for b in bars if b[0] == "Contreventement"} == {"CHS60.3x4C"}


@pytest.mark.parametrize("kw", [dict(n1=4, n2=4, ntr=3), dict(n1=1, n2=2, ntr=1), dict(n1=3, n2=6, ntr=7), dict(n1=2, n2=1, ntr=1)])
def test_cross_beams_connected_to_bracing(kw):
    bars, _ = build_model(_p(**kw))
    arms = [b for b in bars if b[3] == "rigid"]
    for c in (b for b in bars if b[1] == "Poutre transversale" and b[0] != "Extrémité fin"):
        if c[5][1] != pytest.approx(1.16):
            continue
        end = c[5]
        if end[0] > 14:
            continue
        assert any(math.dist(a[4], end) < 1e-6 for a in arms), c


def test_bases_at_zero_and_heights_computed():
    from structures.convoyeur_geom import heights
    for pente in (10, 27.55, 60):
        p = _p(pente=pente)
        _, sup = build_model(p)
        assert all(s[1][2] == 0.0 for s in sup)
        h1, h2, h3 = heights(p)
        assert h1 == 0.4168
        assert h2 - h1 == pytest.approx(pente / 100 * p["L1"])
        assert h3 - h2 == pytest.approx(pente / 100 * p["L2"])
    assert heights(_p()) == pytest.approx((0.4168, 1.9836, 4.3337), abs=2e-3)

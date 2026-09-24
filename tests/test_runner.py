from types import SimpleNamespace

from core import ad_api
from core.runner import run_generation


def _patch(monkeypatch):
    calls = []
    monkeypatch.setattr(ad_api, "check_port", lambda host: calls.append("port"))
    monkeypatch.setattr(ad_api, "new_project", lambda host, fto: calls.append("new"))
    monkeypatch.setattr(ad_api, "open_project", lambda host, fto: calls.append("open"))
    monkeypatch.setattr(ad_api, "close_project", lambda host: calls.append("close"))
    return calls


def test_success_new_project(monkeypatch):
    calls = _patch(monkeypatch)
    lines = []
    s = SimpleNamespace(build=lambda host, p, log: [("Portiques", 5)])
    ok = run_generation(s, {"fto": "C:\\a.fto", "nouveau_projet": True}, "http://h", lines.append)
    assert ok is True
    assert calls == ["port", "new", "close"]
    assert any("Portiques" in l and "5" in l for l in lines)


def test_open_existing(monkeypatch):
    calls = _patch(monkeypatch)
    s = SimpleNamespace(build=lambda host, p, log: [])
    run_generation(s, {"fto": "C:\\a.fto", "nouveau_projet": False}, "http://h", lambda m: None)
    assert calls == ["port", "open", "close"]


def test_error_is_logged_and_project_closed(monkeypatch):
    calls = _patch(monkeypatch)
    lines = []

    def boom(host, p, log):
        raise RuntimeError("API KO")

    ok = run_generation(SimpleNamespace(build=boom), {"fto": "x", "nouveau_projet": True},
                        "http://h", lines.append)
    assert ok is False
    assert calls[-1] == "close"
    assert any("log_erreur" in l for l in lines)


def test_summary_colons_aligned_with_long_labels(monkeypatch):
    _patch(monkeypatch)
    lines = []
    rows = [("Court", 1), ("Section elements CHS88.9x3C tres long", 180)]
    run_generation(SimpleNamespace(build=lambda host, p, log: rows),
                   {"fto": "x", "nouveau_projet": True}, "http://h", lines.append)
    summary = [l for l in lines if l.startswith("  ") and ": " in l]
    assert len(summary) == 2
    assert len({l.index(": ") for l in summary}) == 1

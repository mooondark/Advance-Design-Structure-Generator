import pytest
import requests

from core import ad_api, i18n


class _R:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code, self.payload, self.text = status, payload, text

    def json(self):
        if self.payload is None:
            raise ValueError("pas du JSON")
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def _lang(code):
    i18n.load_language(code)
    i18n.set_scope("common")


@pytest.mark.parametrize("code, word", [("fr", "Erreur API"), ("en", "API error"), ("es", "Error de la API")])
def test_api_error_follows_language(code, word):
    _lang(code)
    bad = _R(200, {"details": {"success": False, "diagnostics": [{"message": "section inconnue"}]}})
    with pytest.raises(RuntimeError) as e:
        ad_api._check(bad, "CreateSection(X)")
    assert word in str(e.value) and "CreateSection(X)" in str(e.value) and "section inconnue" in str(e.value)


def test_http_and_non_json_errors_are_translated():
    _lang("en")
    with pytest.raises(RuntimeError, match=r"\[Op\] HTTP 500"):
        ad_api._check(_R(500, {"x": 1}), "Op")
    with pytest.raises(RuntimeError) as e:
        ad_api._check(_R(200, None, "<html>"), "Op")
    assert "Non-JSON" in str(e.value) and "<html>" in str(e.value)


def test_port_errors_are_translated():
    _lang("fr")
    with pytest.raises(ValueError, match="URL invalide"):
        ad_api.check_port("pas une url")
    _lang("en")
    with pytest.raises(ValueError, match="Invalid URL"):
        ad_api.check_port("pas une url")
    with pytest.raises(ConnectionError, match="Port unreachable: 127.0.0.1:1"):
        ad_api.check_port("http://127.0.0.1:1")


def test_close_project_raises_when_save_fails(monkeypatch):
    _lang("en")
    posted = []
    ko = _R(200, {"details": {"success": False, "diagnostics": [{"message": "PROJECT_SAVE_FAILED"}]}})
    monkeypatch.setattr(ad_api._SESSION, "post", lambda url, **kw: posted.append(url) or ko)
    with pytest.raises(RuntimeError, match="PROJECT_SAVE_FAILED"):
        ad_api.close_project("http://h")
    ad_api.close_project("http://h", save=False)
    assert posted[0].endswith("/CloseProject") and posted[1].endswith("/CloseProjectWithoutSave")


def _service(monkeypatch, version, status=None):
    urls = []

    def get(url, **kw):
        urls.append(url)
        if url.endswith("GetVersion"):
            return _R(200, version) if version else _R(404, None, "Not Found")
        if status is None:
            raise requests.ConnectionError("coupure")
        return _R(200, status)

    monkeypatch.setattr(ad_api._SESSION, "get", get)
    return urls


@pytest.mark.parametrize("version", [None, "1.27.0", "1.9.99.1"])
def test_check_service_skipped_before_1_27_1(monkeypatch, version):
    urls = _service(monkeypatch, version)
    ad_api.check_service("http://h")
    assert not any(u.endswith("GetStatus") for u in urls)


def test_check_service_ok(monkeypatch):
    _service(monkeypatch, "1.27.1.0", {"status": "Ok", "canRun": True})
    ad_api.check_service("http://h")


def test_check_service_refuses_without_licence(monkeypatch):
    _lang("en")
    _service(monkeypatch, "1.28.0", {"status": "Licence_Unavailable", "canRun": False,
                                     "message": None, "licence": {"errorMessage": "No seat available"}})
    with pytest.raises(RuntimeError, match=r"Licence_Unavailable.*No seat available"):
        ad_api.check_service("http://h")


def test_check_service_error_on_status_call(monkeypatch):
    _lang("fr")
    _service(monkeypatch, "1.27.1")
    with pytest.raises(RuntimeError, match="Service API indisponible"):
        ad_api.check_service("http://h")

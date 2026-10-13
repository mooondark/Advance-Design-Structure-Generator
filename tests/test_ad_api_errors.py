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

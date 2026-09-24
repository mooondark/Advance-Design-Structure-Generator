from core import i18n

INI = r"""[common]
a = A commun
x = X commun
fmt = Bonjour {nom}
multi = ligne1\nligne2

[antenna]
x = X antenne
"""


def _load(tmp_path):
    (tmp_path / "fr.ini").write_text(INI, encoding="utf-8")
    i18n.load_language("fr", lang_dir=str(tmp_path))


def test_scope_then_common(tmp_path):
    _load(tmp_path)
    i18n.set_scope("antenna")
    assert i18n.T("x") == "X antenne"
    assert i18n.T("a") == "A commun"
    i18n.set_scope("steel_frame")
    assert i18n.T("x") == "X commun"


def test_format_and_newline(tmp_path):
    _load(tmp_path)
    assert i18n.T("fmt", nom="Bob") == "Bonjour Bob"
    assert i18n.T("multi") == "ligne1\nligne2"


def test_scope_is_per_thread(tmp_path):
    # Streamlit execute chaque session dans son propre thread.
    import threading
    _load(tmp_path)
    i18n.set_scope("antenna")
    seen = []

    def other_session():
        i18n.load_language("fr", lang_dir=str(tmp_path))
        i18n.set_scope("steel_frame")
        seen.append(i18n.T("x"))

    t = threading.Thread(target=other_session)
    t.start()
    t.join()
    assert seen == ["X commun"]
    assert i18n.T("x") == "X antenne"


def test_unknown_placeholder_does_not_crash(tmp_path):
    (tmp_path / "fr.ini").write_text("[common]\nmsg = Section {inconnu} OK\n", encoding="utf-8")
    i18n.load_language("fr", lang_dir=str(tmp_path))
    assert i18n.T("msg", nom="x") == "Section {inconnu} OK"


def test_missing_key_and_file(tmp_path):
    _load(tmp_path)
    assert i18n.T("absente", n=1) == "[absente]"
    i18n.load_language("pl", lang_dir=str(tmp_path))
    assert i18n.T("a") == "[a]"

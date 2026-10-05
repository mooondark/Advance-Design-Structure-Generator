import os

import pytest
from streamlit.testing.v1 import AppTest

from core import config, i18n, runner
from core.profiles import PROFILES

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


@pytest.fixture
def cfg_file(tmp_path, monkeypatch):
    path = tmp_path / "config.ini"
    monkeypatch.setattr(config, "CONFIG_FILE", str(path))
    # AppTest appelle format_func dans le thread du test : il lui faut la langue de l'app.
    i18n.load_language("fr")
    return path


def _run():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, at.exception
    return at


def test_both_structures_render(cfg_file):
    at = _run()
    at.selectbox(key="structure@fr").set_value("antenna").run()
    assert not at.exception, at.exception
    assert config.load_config()["structure"] == "antenna"


def test_values_survive_structure_switch(cfg_file):
    at = _run()
    at.number_input(key="steel_frame.n").set_value(7).run()
    at.selectbox(key="structure@fr").set_value("antenna").run()
    at.selectbox(key="structure@fr").set_value("steel_frame").run()
    assert not at.exception, at.exception
    assert at.number_input(key="steel_frame.n").value == 7


def test_family_change_resets_profile(cfg_file):
    at = _run()
    at.selectbox(key="steel_frame.Sp.fam").set_value("IPE").run()
    assert not at.exception, at.exception
    assert at.selectbox(key="steel_frame.Sp").value == PROFILES["IPE"][0]


def test_unknown_structure_in_config(cfg_file):
    cfg_file.write_text("[General]\nstructure = retiree\n", encoding="utf-8")
    at = _run()
    assert at.selectbox(key="structure@fr").value == "steel_frame"


def test_invalid_guy_heights_preview(cfg_file):
    at = _run()
    at.selectbox(key="structure@fr").set_value("antenna").run()
    at.number_input(key="antenna.guy_levels").set_value(2).run()
    at.text_input(key="antenna.guy_heights").set_value("abc").run()
    assert not at.exception, at.exception
    assert len(at.info) == 1


@pytest.fixture
def generated(cfg_file, monkeypatch):
    # Generation simulee reussie : AppTest reexecute app.py, qui reimporte run_generation depuis core.runner.
    monkeypatch.setattr(runner, "run_generation", lambda s, p, host, log: True)
    at = _run()
    at.button(key="generate").click().run()
    assert not at.exception, at.exception
    assert len(at.success) == 1
    return at


def test_result_kept_on_plain_rerun(generated):
    generated.run()
    assert len(generated.success) == 1


def test_result_cleared_on_option_change(generated):
    generated.number_input(key="steel_frame.n").set_value(6).run()
    assert len(generated.success) == 0


def test_result_cleared_on_structure_change(generated):
    generated.selectbox(key="structure@fr").set_value("antenna").run()
    assert len(generated.success) == 0


def test_result_cleared_on_project_change(generated):
    generated.text_input(key="project.name").set_value("autre").run()
    assert len(generated.success) == 0


class _FakeApi:
    def poll(self):
        return None

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0


def test_result_cleared_on_api_stop(generated):
    generated.session_state["api_proc"] = _FakeApi()
    generated.run()
    generated.button(key="api_stop").click().run()
    assert not generated.exception, generated.exception
    assert len(generated.success) == 0


@pytest.mark.parametrize("lang, site", [("fr", "https://graitec.com/fr/"),
                                         ("en", "https://graitec.com/uk/"),
                                         ("pl", "https://graitec.com/pl/"),
                                         ("es", "https://graitec.com/es/"),
                                         ("pt", "https://graitec.com/pt/")])
def test_footer_links_follow_language(cfg_file, lang, site):
    at = _run()
    at.selectbox(key="settings.lang").set_value(lang).run()
    footer = [c.value for c in at.caption if "github.com/mooondark" in c.value]
    assert len(footer) == 1
    assert "https://github.com/mooondark/Advance-Design-Structure-Generator" in footer[0]
    assert "https://github.com/Graitec-Group/advance-design-api" in footer[0]
    assert site in footer[0]
    assert "[footer_" not in footer[0]


def _concrete(at):
    at.selectbox(key="structure@fr").set_value("concrete_frame").run()
    assert not at.exception, at.exception
    return at


def test_concrete_shape_switch_changes_dimension_fields(cfg_file):
    at = _concrete(_run())
    keys = [w.key for w in at.number_input]
    assert "concrete_frame.Sbr.d2" in keys
    at.selectbox(key="concrete_frame:Sbr:shape@fr").set_value("C").run()
    assert "concrete_frame.Sbr.d2" not in [w.key for w in at.number_input]
    assert at.session_state["concrete_frame.Sbr"].startswith("C")


def test_concrete_dimensions_build_section_name(cfg_file):
    at = _concrete(_run())
    at.number_input(key="concrete_frame.Sbr.d1").set_value(25).run()
    at.number_input(key="concrete_frame.Sbr.d2").set_value(60).run()
    assert at.session_state["concrete_frame.Sbr"] == "R25*60"


def test_concrete_ne_fills_heights(cfg_file):
    at = _concrete(_run())
    at.number_input(key="concrete_frame.Ne").set_value(3).run()
    assert at.text_input(key="concrete_frame.He").value == "3.0,3.0,3.0"


def test_concrete_ne_with_unreadable_heights(cfg_file):
    at = _concrete(_run())
    at.text_input(key="concrete_frame.He").set_value("abc").run()
    assert not at.exception, at.exception
    assert len(at.info) == 1
    at.number_input(key="concrete_frame.Ne").set_value(2).run()
    assert not at.exception, at.exception
    assert at.text_input(key="concrete_frame.He").value == "3.0,3.0"


def test_concrete_dimensions_survive_structure_switch(cfg_file):
    at = _concrete(_run())
    at.number_input(key="concrete_frame.Spf.d1").set_value(45).run()
    at.selectbox(key="structure@fr").set_value("steel_frame").run()
    at.selectbox(key="structure@fr").set_value("concrete_frame").run()
    assert at.number_input(key="concrete_frame.Spf.d1").value == 45
    assert at.session_state["concrete_frame.Spf"] == "C45"


def _switch_language(at, current, new):
    # AppTest formate les options dans le thread du test : il lui faut la langue affichee par l'app.
    i18n.load_language(current)
    at.selectbox(key="settings.lang").set_value(new).run()
    i18n.load_language(new)
    assert not at.exception, at.exception


def test_language_round_trip_keeps_translated_choices(cfg_file):
    # Streamlit memorise le libelle affiche d'une selectbox / segmented_control : apres FR -> PL -> FR,
    # l'ancien libelle ne doit jamais etre relu (bug KeyError 'Portique béton').
    at = _concrete(_run())
    at.selectbox(key="concrete_frame:Sbr:shape@fr").set_value("C").run()
    _switch_language(at, "fr", "pl")
    assert "structure@pl" in [w.key for w in at.selectbox]
    _switch_language(at, "pl", "fr")
    assert at.session_state["structure"] == "concrete_frame"
    assert at.session_state["concrete_frame.Sbr.shape"] == "C"
    assert at.session_state["concrete_frame.TypeAppui"] == "FIXED"
    assert at.selectbox(key="structure@fr").value == "concrete_frame"


def test_hidden_structure_not_offered(cfg_file):
    cfg_file.write_text("[General]\nView_Antenna = false\n", encoding="utf-8")
    at = _run()
    options = at.selectbox(key="structure@fr").options
    assert "Pylône antenne" not in options and len(options) == 2


def test_saved_structure_hidden_falls_back_to_first_visible(cfg_file):
    cfg_file.write_text("[General]\nstructure = antenna\nView_Antenna = 0\n", encoding="utf-8")
    at = _run()
    assert at.selectbox(key="structure@fr").value == "steel_frame"


def _convoyeur(cfg_file):
    cfg_file.write_text("[General]\nView_Convoyeur = True\n", encoding="utf-8")
    at = _run()
    at.selectbox(key="structure@fr").set_value("convoyeur").run()
    assert not at.exception, at.exception
    return at


def test_convoyeur_hidden_by_default_and_key_created(cfg_file):
    at = _run()
    assert "Convoyeur" not in " ".join(at.selectbox(key="structure@fr").options)
    assert "View_Convoyeur = False" in cfg_file.read_text(encoding="utf-8")


def test_convoyeur_renders_when_enabled(cfg_file):
    at = _convoyeur(cfg_file)
    assert at.selectbox(key="structure@fr").value == "convoyeur"
    assert at.number_input(key="convoyeur.pente").value == 27.5


def test_saved_convoyeur_hidden_falls_back_to_first_visible(cfg_file):
    cfg_file.write_text("[General]\nstructure = convoyeur\n", encoding="utf-8")
    at = _run()
    assert at.selectbox(key="structure@fr").value == "steel_frame"


def test_convoyeur_family_change_resets_profile(cfg_file):
    at = _convoyeur(cfg_file)
    at.selectbox(key="convoyeur.Sc.fam").set_value("CHSH").run()
    assert not at.exception, at.exception
    assert at.selectbox(key="convoyeur.Sc").value == PROFILES["CHSH"][0]


def test_convoyeur_cs2_fields_apply_section_twice(cfg_file):
    at = _convoyeur(cfg_file)
    assert at.session_state["convoyeur.S31"] == "CS2 I17.5*0.8+9*0.5 I17.5*0.8+9*0.5"
    at.number_input(key="convoyeur.S31.d1").set_value(1.1).run()
    at.number_input(key="convoyeur.S31.d2").set_value(17.5).run()
    at.number_input(key="convoyeur.S31.d3").set_value(0.75).run()
    assert not at.exception, at.exception
    assert at.session_state["convoyeur.S31"] == "CS2 I17.5*1.1+17.5*0.75 I17.5*1.1+17.5*0.75"


def test_convoyeur_parametric_dimensions_survive_family_round_trip(cfg_file):
    at = _convoyeur(cfg_file)
    at.number_input(key="convoyeur.S1.d0").set_value(20.0).run()
    at.selectbox(key="convoyeur.S1.fam").set_value("HEA").run()
    assert not at.exception, at.exception
    at.selectbox(key="convoyeur.S1.fam").set_value("I*").run()
    assert not at.exception, at.exception
    assert at.session_state["convoyeur.S1"] == "I20*1.1+17.5*0.75"


def test_convoyeur_language_round_trip(cfg_file):
    at = _convoyeur(cfg_file)
    _switch_language(at, "fr", "pl")
    _switch_language(at, "pl", "fr")
    assert at.session_state["structure"] == "convoyeur"
    assert at.selectbox(key="structure@fr").value == "convoyeur"

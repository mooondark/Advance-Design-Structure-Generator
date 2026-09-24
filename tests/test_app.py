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
    at.selectbox(key="structure").set_value("antenna").run()
    assert not at.exception, at.exception
    assert config.load_config()["structure"] == "antenna"


def test_values_survive_structure_switch(cfg_file):
    at = _run()
    at.number_input(key="steel_frame.n").set_value(7).run()
    at.selectbox(key="structure").set_value("antenna").run()
    at.selectbox(key="structure").set_value("steel_frame").run()
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
    assert at.selectbox(key="structure").value == "steel_frame"


def test_invalid_guy_heights_preview(cfg_file):
    at = _run()
    at.selectbox(key="structure").set_value("antenna").run()
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
    generated.selectbox(key="structure").set_value("antenna").run()
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
                                         ("pl", "https://graitec.com/pl/")])
def test_footer_links_follow_language(cfg_file, lang, site):
    at = _run()
    at.selectbox(key="settings.lang").set_value(lang).run()
    footer = [c.value for c in at.caption if "github.com/mooondark" in c.value]
    assert len(footer) == 1
    assert "https://github.com/mooondark/Advance-Design-Structure-Generator" in footer[0]
    assert "https://github.com/Graitec-Group/advance-design-api" in footer[0]
    assert site in footer[0]
    assert "[footer_" not in footer[0]

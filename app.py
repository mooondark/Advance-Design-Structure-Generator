"""
Structure Generator : generation de structures metalliques parametriques
via l'API Advance Design (Graitec).

Lancement : streamlit run app.py   (ou double-clic sur start.bat)
"""
import os
import sys

import streamlit as st

from core import i18n, ui
from core.config import save_config
from core.i18n import T
from core.runner import run_generation
from structures import STRUCTURES

VERSION = "2.1"

# Sentinelle d'environnement pour le worker Streamlit en mode PyInstaller.
_SG_STREAMLIT_WORKER = "_SG_STREAMLIT_WORKER"


def _generate(structure, p):
    fto = ui.project_path()
    if fto is None:
        st.stop()
    p = {**p, "fto": fto, "nouveau_projet": st.session_state["project.new"]}
    try:
        structure.validate(p)
    except ValueError as ex:
        st.error(str(ex))
        st.stop()
    host = st.session_state["settings.host"].strip().rstrip("/")
    lines = []
    with st.spinner(T("ui_generation_en_cours")):
        ok = run_generation(structure, p, host, lines.append)
    st.session_state.log_lines = lines
    st.session_state.last_result = "ok" if ok else "error"
    st.rerun()


def main():
    st.set_page_config(page_title="Structure Generator", page_icon=":material/foundation:",
                       layout="wide", initial_sidebar_state="collapsed")
    ui.init_session()
    ui.keep_widget_state()
    key = st.session_state.structure
    structure = STRUCTURES[key]
    i18n.load_language(st.session_state["settings.lang"])
    i18n.set_scope(key)
    ui.inject_css()

    h1, h2 = st.columns([3, 1], vertical_alignment="center")
    h1.subheader(f"{structure.ICON} Structure Generator  v{VERSION}")
    h2.selectbox(T("ui_structure"), list(STRUCTURES), format_func=lambda k: T(STRUCTURES[k].TITLE_KEY),
                 key="structure", label_visibility="collapsed",
                 on_change=lambda: save_config(structure=st.session_state.structure))

    col_form, col_preview = st.columns([2, 1], gap="medium")
    with col_form:
        ui.settings_panel()
        ui.project_panel()
        structure.render_form()
        ui.sections_panel(key, structure.ELEMENTS)
    p = ui.collect_params(key, structure)
    with col_preview:
        ui.preview_panel(key, p)

    col_actions, col_journal = st.columns([2, 1], gap="medium")
    with col_actions:
        clicked = ui.actions_row()
    with col_journal:
        ui.journal_button()

    if clicked:
        _generate(structure, p)


def _launch_as_exe():
    """Lanceur PyInstaller : relance l'exe avec la sentinelle puis ouvre le navigateur."""
    import subprocess
    import threading
    import time
    import webbrowser

    env = os.environ.copy()
    env[_SG_STREAMLIT_WORKER] = "1"
    env["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    proc = subprocess.Popen([sys.executable], env=env)

    def _open_browser():
        time.sleep(4)
        webbrowser.open("http://localhost:8501")

    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        if os.environ.get(_SG_STREAMLIT_WORKER) == "1":
            from streamlit.web import cli as _st_cli
            # config.toml n'est pas embarque en mode exe : theme passe en argv.
            sys.argv = [
                "streamlit", "run", os.path.join(sys._MEIPASS, "app.py"),
                "--server.port", "8501",
                "--server.address", "localhost",
                "--server.headless", "true",
                "--global.developmentMode", "false",
                "--browser.gatherUsageStats", "false",
                "--theme.base", "dark",
                "--theme.primaryColor", "#1d4ed8",
                "--theme.backgroundColor", "#0f1623",
                "--theme.secondaryBackgroundColor", "#1e2634",
                "--theme.textColor", "#e2e8f0",
            ]
            _st_cli.main(standalone_mode=False)
        else:
            _launch_as_exe()
    else:
        main()

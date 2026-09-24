"""Blocs d'interface communs a toutes les structures."""
import os
import subprocess

import streamlit as st

from core import ad_api
from core.config import load_config, save_config
from core.i18n import LANG_LABELS, T, load_language
from core.layout import section
from core.profiles import PROFILES
from structures import STRUCTURES

PREVIEW_HEIGHT = 600
DEFAULT_HOST = "http://localhost:52000"

_CSS = """
<style>
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }

    /* 3.4rem : le contenu commence sous la barre Streamlit (60 px, opaque) */
    .block-container { padding-top: 3.4rem !important; padding-bottom: 0.5rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }

    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextInput"] input {
        padding-top: 4px !important;
        padding-bottom: 4px !important;
        height: 34px !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stNumberInput"] > div,
    div[data-testid="stTextInput"]   > div { min-height: 34px !important; }

    div[data-testid="stNumberInput"] button {
        height: 34px !important;
        padding: 0 6px !important;
    }

    div[data-testid="stSelectbox"] > div > div {
        padding-top: 4px !important;
        padding-bottom: 4px !important;
        min-height: 34px !important;
        font-size: 0.88rem !important;
    }

    li[role="option"] {
        padding-top: 4px !important;
        padding-bottom: 4px !important;
        font-size: 0.88rem !important;
        min-height: 28px !important;
    }

    div[data-testid="stNumberInput"] label,
    div[data-testid="stTextInput"]   label,
    div[data-testid="stSelectbox"]   label {
        font-size: 0.8rem !important;
        margin-bottom: 1px !important;
        padding-bottom: 0 !important;
    }

    div[data-testid="stCheckbox"] { margin-top: 4px !important; margin-bottom: 2px !important; }
    div[data-testid="stCheckbox"] label { font-size: 0.88rem !important; }

    details summary { padding: 6px 10px !important; font-size: 0.88rem !important; }

    h3 { padding: 0 !important; }

    /* Cadres de section (core/layout.py) : titre pose sur la bordure */
    div[class*="st-key-sec_"] { position: relative; overflow: visible; margin-top: 0.55rem;
                                padding: 0.85rem 0.9rem 0.7rem !important; }
    div[class*="st-key-sec_"] > div.stElementContainer:first-child { position: absolute; top: -0.72rem; left: 0.7rem;
                                                                     width: auto !important; z-index: 1; }
    div[class*="st-key-sec_"] > div.stElementContainer:first-child p { padding: 0 0.4rem; margin: 0; line-height: 1.4; }
    /* Le titre masque le trait avec le fond de page : heritage depuis stApp, suit le changement de theme sans rerun */
    [data-testid="stApp"] :has(div[class*="st-key-sec_"]),
    div[class*="st-key-sec_"],
    div[class*="st-key-sec_"] > div.stElementContainer:first-child,
    div[class*="st-key-sec_"] > div.stElementContainer:first-child * { background-color: inherit !important; }
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def init_session():
    ss = st.session_state
    if "structure" in ss:
        return
    cfg = load_config()
    defaults = {
        "structure": cfg["structure"] if cfg["structure"] in STRUCTURES else next(iter(STRUCTURES)),
        "settings.lang": cfg["language"] if cfg["language"] in LANG_LABELS else "fr",
        "settings.exe": cfg["api_server_exe"],
        "settings.host": DEFAULT_HOST,
        "project.new": True,
        "project.name": "nouveau_projet",
        "project.fto": "",
        "log_lines": [],
        "last_result": None,
        "api_proc": None,
    }
    for skey, s in STRUCTURES.items():
        for name, value in s.DEFAULTS.items():
            defaults[f"{skey}.{name}"] = value
        for name, (_label, families, profile) in s.ELEMENTS.items():
            defaults[f"{skey}.{name}"] = profile
            defaults[f"{skey}.{name}.fam"] = next(f for f in families if profile in PROFILES[f])
        defaults[f"{skey}.M"] = s.DEFAULT_MATERIAL
    for k, v in defaults.items():
        ss[k] = v


def keep_widget_state():
    # Streamlit efface l'etat d'un widget non affiche : on reinjecte les cles "a.b".
    for k in list(st.session_state.keys()):
        if "." in k:
            st.session_state[k] = st.session_state[k]


def native_pick(save, initial=""):
    """Boite de dialogue systeme (tkinter). Chemin, '' si annule, None si indisponible."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    kw = {"title": T("browse_title_fto"),
          "filetypes": [("Advance Design (*.fto)", "*.fto"), ("*.*", "*.*")]}
    if initial:
        d = os.path.dirname(initial)
        if os.path.isdir(d):
            kw["initialdir"] = d
        if os.path.basename(initial):
            kw["initialfile"] = os.path.basename(initial)
    if save:
        path = filedialog.asksaveasfilename(defaultextension=".fto", **kw)
    else:
        path = filedialog.askopenfilename(**kw)
    root.destroy()
    return os.path.normpath(path) if path else ""


def _browse():
    ss = st.session_state
    # Callback : s'execute avant main(), dans un thread ou la langue n'est pas encore chargee.
    load_language(ss["settings.lang"])
    field = "project.name" if ss["project.new"] else "project.fto"
    res = native_pick(save=ss["project.new"], initial=ss[field])
    if res is None:
        ss["_no_dialog"] = True
    elif res:
        ss[field] = res


def settings_panel():
    with st.expander(T("ui_params_expander"), expanded=False):
        c1, c2 = st.columns([1, 2])
        c1.selectbox(T("ui_language"), list(LANG_LABELS), format_func=LANG_LABELS.get,
                     key="settings.lang", on_change=lambda: save_config(language=st.session_state["settings.lang"]))
        c2.text_input(T("ui_url_api_ad"), key="settings.host")
        st.text_input(T("ui_chemin_exe"), key="settings.exe",
                      on_change=lambda: save_config(api_server_exe=st.session_state["settings.exe"]))


def _api_block():
    ss = st.session_state
    proc = ss.api_proc
    # Pas de legende d'etat : le libelle du bouton (Demarrer / Arreter) porte l'etat, 35 px gagnes en 1080p.
    if proc is not None and proc.poll() is None:
        if st.button(T("ui_btn_stop_api"), key="api_stop", icon=":material/stop:", help=T("ui_api_active"),
                     width="stretch"):
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            ss.api_proc = None
            ss.last_result = None
            st.rerun()
    else:
        if st.button(T("ui_btn_start_api"), icon=":material/play_arrow:", help=T("ui_api_inactive"),
                     width="stretch"):
            exe = os.path.normpath(ss["settings.exe"])
            if not os.path.isfile(exe):
                st.error(T("err_api_server_exe_not_found", path=exe))
            else:
                try:
                    ss.api_proc = subprocess.Popen([exe, "/console"], cwd=os.path.dirname(exe) or None)
                    st.rerun()
                except OSError as e:
                    st.error(T("err_api_server_start_failed", details=str(e)))


def project_panel():
    ss = st.session_state
    pj1, pj2, pj3 = section("projet", ":material/folder:", T("ui_web_projet")).columns(
        [1, 2, 1], vertical_alignment="bottom")
    pj1.checkbox(T("ui_nouveau_fichier"), key="project.new")
    with pj2:
        tc, bc = st.columns([5, 1], vertical_alignment="bottom")
        if ss["project.new"]:
            tc.text_input(T("ui_nouveau_nom"), key="project.name")
        else:
            tc.text_input(T("ui_fichier_existant"), key="project.fto", placeholder=r"C:\Projets\mon_projet.fto")
        bc.button("", key="browse_fto", icon=":material/folder_open:", help=T("ui_btn_parcourir"),
                  width="stretch", on_click=_browse)
    with pj3:
        _api_block()
    if ss.pop("_no_dialog", False):
        st.warning(T("ui_dialog_indispo"))


def sections_panel(key, elements):
    ss = st.session_state
    box = section("sections", ":material/hardware:", T("ui_web_sections"))
    items = list(elements.items()) + [("M", None)]
    for i in range(0, len(items), 2):
        cols = box.columns([1, 2, 1, 2])
        for j, (name, spec) in enumerate(items[i:i + 2]):
            c_fam, c_prof = cols[2 * j], cols[2 * j + 1]
            if spec is None:
                c_fam.selectbox(T("ui_materiau"), ad_api.MATERIALS, key=f"{key}.M")
                continue
            label_key, families, _default = spec
            fam = c_fam.selectbox(T(label_key), families, key=f"{key}.{name}.fam")
            names = PROFILES[fam]
            if ss[f"{key}.{name}"] not in names:
                ss[f"{key}.{name}"] = names[0]
            c_prof.selectbox(T(label_key), names, key=f"{key}.{name}", label_visibility="hidden")


def collect_params(key, structure):
    names = list(structure.DEFAULTS) + list(structure.ELEMENTS) + ["M"]
    return {n: st.session_state[f"{key}.{n}"] for n in names}


def form_state(key, p):
    """Empreinte de tout ce que l'utilisateur peut modifier : le resultat affiche ne vaut que pour elle."""
    ss = st.session_state
    return repr((key, sorted(p.items()), ss["project.new"], ss["project.name"], ss["project.fto"],
                 ss["settings.host"]))


def project_path():
    ss = st.session_state
    if ss["project.new"]:
        nom = ss["project.name"].strip()
        if not nom:
            st.error(T("ui_projet_obligatoire"))
            return None
        if not nom.lower().endswith(".fto"):
            nom += ".fto"
        path = os.path.join(os.getcwd(), nom)
    else:
        path = ss["project.fto"].strip()
        if not path:
            st.error(T("ui_chemin_obligatoire"))
            return None
    return os.path.normpath(path)  # l'API AD exige des separateurs "\"


@st.cache_data(show_spinner=False, max_entries=32)
def _figure(key, p):
    fig = STRUCTURES[key].preview(p)
    fig.update_layout(height=PREVIEW_HEIGHT)
    return fig


def preview_panel(key, p):
    try:
        fig = _figure(key, p)
    except Exception:
        st.info(T("ui_apercu_indisponible"))
        return
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": True, "displaylogo": False})


def actions_row():
    c1, c2, c3 = st.columns([3, 1, 3])
    clicked = c1.button(T("ui_btn_creer"), key="generate", icon=":material/play_arrow:", type="primary",
                        width="stretch")
    if c2.button("", icon=":material/delete:", help=T("ui_btn_effacer"), width="stretch"):
        st.session_state.log_lines = []
        st.session_state.last_result = None
        st.rerun()
    with c3:
        if st.session_state.last_result == "error":
            st.error(T("ui_generation_echouee"))
        elif st.session_state.last_result == "ok":
            st.success(T("ui_generation_reussie"))
    return clicked


def footer():
    st.divider()
    st.caption(f"[{T('footer_github')}](https://github.com/mooondark/Advance-Design-Structure-Generator) - "
               f"[{T('footer_api')}](https://github.com/Graitec-Group/advance-design-api) - "
               f"[{T('footer_site')}]({T('footer_site_url')})", text_alignment="center")


def _journal_body():
    st.code("\n".join(st.session_state.log_lines), language=None, height=500)


def journal_button():
    if st.button(T("ui_btn_ouvrir_journal"), icon=":material/receipt_long:", width="stretch",
                 disabled=not st.session_state.log_lines):
        st.dialog(T("ui_journal_execution"), width="large")(_journal_body)()

"""Convoyeur a bande incline : 3 portiques, 2 travees, contreventement, extremites debut et fin."""
import streamlit as st

from core import ad_api
from core.i18n import T
from core.layout import section
from structures.convoyeur_geom import build_model, heights

KEY = "convoyeur"
TITLE_KEY = "structure_convoyeur"
ICON = ":material/conveyor_belt:"
# Structure cachee tant que View_Convoyeur n'est pas passee a True dans config.ini.
VISIBLE_BY_DEFAULT = False
MATERIALS = ad_api.STEEL_GRADES
DEFAULT_MATERIAL = "S275"
SUPPORT_MATERIAL = "C25/30"
# Camera 3D par defaut : vue de cote (depuis -Y), legerement en hauteur et vers le debut du convoyeur.
CAMERA_EYE = dict(x=-2, y=-3, z=0.7)
_I = ["I*", "HEA", "HEB", "HEM", "IPE"]
_CHS = ["CHSC", "CHSH"]
_BRACING = _CHS + ["SHSC", "SHSH", "L", "UPE", "UPN"]
ELEMENTS = {
    "Sc":  ("ui_sec_contrev",  _BRACING,                              "CHS42.4x4C"),
    "Sd":  ("ui_sec_diag",     _BRACING,                              "CHS60.3x4C"),
    "St":  ("ui_sec_transv",   ["U*", "I*", "UPN", "UPE", "C", "IPE", "HEA", "HEB"],         "U12*0.55+5.3*0.8"),
    "Sm":  ("ui_sec_princ",    _I,                                "I68*1+18*0.5"),
    "S1":  ("ui_sec_p1",       _I,                                "I17.5*1.1+17.5*0.75"),
    "S2":  ("ui_sec_p2",       _I,                                "I17.5*0.8+9*0.5"),
    "S31": ("ui_sec_p31",      _I + ["CS2"],                      "CS2 I17.5*0.8+9*0.5 I17.5*0.8+9*0.5"),
    "S32": ("ui_sec_p32",      _I,                                "I17.5*0.8+9*0.5"),
    "Sx":  ("ui_sec_traverse", ["SHSC", "SHSH", "CHSC", "CHSH"],  "SHS60x4C"),
    "Sdb": ("ui_sec_pdeb",     _I,                                "I68*1+18*0.5"),
    "Sdu": ("ui_sec_udeb",     ["UPN", "UPE", "U*"],              "UPN220"),
}
DEFAULTS = {
    "pente": 27.5, "Em": 1.16, "debord": 0.8, "L1": 5.7, "L2": 8.5, "Ldeb": 1.6,
    "n1": 4, "n2": 6, "ntr": 4,
    "H1": 0.5, "Hs3": 1.3, "Ne2": 2, "Ne3": 3,
    "E1": 1.16, "E2": 1.5, "E3": 2.0,
}
SYSTEMS_ROOT = ("Portique 1", "Portique 2", "Portique 3", "Rigides")
SYSTEMS_CONVOYEUR = ("Travée 1", "Travée 2", "Extrémité fin", "Contreventement", "Extrémité début")


def _k(name):
    return f"{KEY}.{name}"


def _float(col, label_key, name, step=0.1, high=999.0):
    col.number_input(T(label_key), min_value=0.001, max_value=high, step=step, format="%.3f", key=_k(name))


def _int(col, label_key, name):
    col.number_input(T(label_key), min_value=1, max_value=99, step=1, key=_k(name))


def render_form():
    g = section("geo", ":material/square_foot:", T("ui_web_geo")).columns(3)
    _float(g[0], "ui_pente", "pente", 0.1, 100.0)
    _float(g[0], "ui_em", "Em")
    _float(g[1], "ui_l1", "L1")
    _float(g[1], "ui_l2", "L2")
    _float(g[2], "ui_debord", "debord")
    _float(g[2], "ui_ldeb", "Ldeb")

    t = section("trav", ":material/straighten:", T("ui_web_trav")).columns(3)
    _int(t[0], "ui_n1", "n1")
    _int(t[1], "ui_n2", "n2")
    _int(t[2], "ui_ntr", "ntr")

    p = section("port", ":material/foundation:", T("ui_web_port")).columns(3)
    h = heights({n: st.session_state[_k(n)] for n in ("H1", "pente", "L1", "L2")})
    _float(p[0], "ui_h1", "H1")
    _float(p[0], "ui_e1", "E1")
    p[1].text_input(T("ui_h2"), value=f"{h[1]:.3f}", disabled=True)
    _float(p[1], "ui_e2", "E2")
    _int(p[1], "ui_ne2", "Ne2")
    p[2].text_input(T("ui_h3"), value=f"{h[2]:.3f}", disabled=True)
    _float(p[2], "ui_e3", "E3")
    _int(p[2], "ui_ne3", "Ne3")
    _float(p[2], "ui_hs3", "Hs3")


def preview(p):
    import plotly.graph_objects as go

    bars, supports = build_model(p)

    def lines(segs, color, width):
        xs, ys, zs = [], [], []
        for a, b in segs:
            xs += [a[0], b[0], None]
            ys += [a[1], b[1], None]
            zs += [a[2], b[2], None]
        return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines",
                            line=dict(color=color, width=width), hoverinfo="skip")

    fig = go.Figure([
        lines([(b[4], b[5]) for b in bars if b[3] != "rigid"], "#4A7FE0", 4),
        lines([(b[4], b[5]) for b in bars if b[3] == "rigid"], "#2CB67D", 2),
        go.Scatter3d(x=[s[1][0] for s in supports], y=[s[1][1] for s in supports], z=[s[1][2] for s in supports],
                     mode="markers", hoverinfo="skip",
                     marker=dict(size=4, color="#E8A840", symbol="diamond")),
    ])
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            aspectmode="data",
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            camera=dict(projection=dict(type="perspective"),
                        eye=CAMERA_EYE),
        ),
    )
    return fig


def validate(p):
    errors = []
    positives = ["pente", "Em", "debord", "L1", "L2", "Ldeb", "H1", "Hs3", "E1", "E2", "E3"]
    if any(p[n] <= 0 for n in positives):
        errors.append(T("val_conv_pos"))
    if any(p[n] < 1 for n in ("n1", "n2", "ntr", "Ne2", "Ne3")) or p["n1"] + p["n2"] < 3 \
            or (p["n1"] + p["n2"] - 2) % p["ntr"] != 0:
        errors.append(T("val_conv_n"))
    if p["Hs3"] >= heights(p)[2]:
        errors.append(T("val_conv_hs3"))
    if errors:
        raise ValueError("\n".join(errors))


def build(host, p, log):
    bars, supports = build_model(p)

    log(T("log_materiau", nom=p["M"]))
    mat = ad_api.create_material(host, p["M"])
    log(T("log_materiau_ok", nom=p["M"], eid=mat))
    rigid = ad_api.create_material(host, "Rigid")
    support_mat = ad_api.create_material(host, SUPPORT_MATERIAL)

    # Toutes les sections avant les systemes et les elements (CreateSection peut etre lent sur un modele rempli).
    log(T("log_conv_sections"))
    sections = {name: ad_api.create_section(host, name) for name in dict.fromkeys(b[2] for b in bars)}

    log(T("log_conv_systemes"))
    systems = {name: ad_api.create_system(host, name, parent_eid=0) for name in SYSTEMS_ROOT}
    convoyeur = ad_api.create_system(host, "Convoyeur", parent_eid=0)
    systems["Convoyeur"] = convoyeur
    for name in SYSTEMS_CONVOYEUR:
        systems[name] = ad_api.create_system(host, name, parent_eid=convoyeur)
    ad_api.create_system(host, "Points", parent_eid=0)

    log(T("log_conv_barres", n=len(bars)))
    for sysname, name, secname, kind, a, b in bars:
        ad_api.create_linear_element(host, a, b, rigid if kind == "rigid" else mat, sections[secname], kind,
                                     user_name=name, system_ids=[systems[sysname]])

    log(T("log_conv_appuis", n=len(supports)))
    for sysname, pt in supports:
        ad_api.create_support(host, pt, support_mat, "FIXED", user_name="Appui", system_ids=[systems[sysname]])

    n_rigid = sum(1 for b in bars if b[3] == "rigid")
    return [
        (T("syn_conv_pente"), f"{p['pente']} %"),
        (T("syn_conv_barres"), len(bars) - n_rigid),
        (T("syn_conv_rigides"), n_rigid),
        (T("syn_appuis"), len(supports)),
        (T("syn_total"), len(bars) + len(supports)),
    ]

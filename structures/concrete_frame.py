"""Portique beton arme multi-etages : poteaux, poutres excentrees vers le bas, dalles, systemes par etage."""
import math

import streamlit as st

from core import ad_api
from core.concrete import parse_section, section_height
from core.i18n import T
from core.layout import choice, section

KEY = "concrete_frame"
TITLE_KEY = "structure_concrete_frame"
ICON = ":material/apartment:"
MATERIALS = list(ad_api.CONCRETE_PROPS)
DEFAULT_MATERIAL = "C25/30"
ELEMENTS = {
    "Spf": ("ui_sec_poteaux_facade", "beton", "C30"),
    "Spi": ("ui_sec_poteaux_int",    "beton", "C20"),
    "Sbr": ("ui_sec_poutres_rive",   "beton", "R20*50"),
    "Sbi": ("ui_sec_poutres_int",    "beton", "R20*70"),
}
DEFAULTS = {
    "Nx": 2, "Ny": 4, "Lx": 5.0, "Ly": 5.0,
    "Ne": 1, "He": "3.0", "Ep": 0.20,
    "TypeAppui": "FIXED",
    "creer_systemes": True,
}
APPUIS = ["HINGED", "FIXED"]
SUB_SYSTEMS = ["POTEAU", "VOILE", "POUTRE", "DALLE"]
# Poutre sous le plancher, fibre superieure au niveau (verifie dans AD : "centre_haut" la placait au-dessus).
POUTRE_EXCENTRATION = "centre_bas"
# Excentrement de dalle en fraction de Ep : -0.5 place la face superieure au niveau (verifie dans AD).
DALLE_EXCENTREMENT = -0.5


def _k(name):
    return f"{KEY}.{name}"


def parse_heights(text):
    return [float(x) for x in (text or "").split(",") if x.strip()]


def heights(p):
    he = parse_heights(p["He"])
    return he * int(p["Ne"]) if len(he) == 1 else he


def levels(p):
    z = [0.0]
    for h in heights(p):
        z.append(round(z[-1] + h, 6))
    return z


def _geometry(p):
    nx, ny = int(p["Nx"]), int(p["Ny"])
    lx, ly = float(p["Lx"]), float(p["Ly"])
    z = levels(p)
    xs = [i * lx for i in range(nx + 1)]
    ys = [j * ly for j in range(ny + 1)]
    columns, beams, slabs = [], [], []
    for k in range(1, len(z)):
        for i in range(nx + 1):
            for j in range(ny + 1):
                columns.append({"level": k - 1, "facade": i in (0, nx) or j in (0, ny),
                                "start": (xs[i], ys[j], z[k - 1]), "end": (xs[i], ys[j], z[k])})
        for j in range(ny + 1):
            for i in range(nx):
                beams.append({"level": k, "rive": j in (0, ny),
                              "start": (xs[i], ys[j], z[k]), "end": (xs[i + 1], ys[j], z[k])})
        for i in range(nx + 1):
            for j in range(ny):
                beams.append({"level": k, "rive": i in (0, nx),
                              "start": (xs[i], ys[j], z[k]), "end": (xs[i], ys[j + 1], z[k])})
        slabs.append({"level": k, "pts": [(0.0, 0.0, z[k]), (xs[-1], 0.0, z[k]),
                                          (xs[-1], ys[-1], z[k]), (0.0, ys[-1], z[k])]})
    supports = [(x, y, 0.0) for x in xs for y in ys]
    return columns, beams, slabs, supports, z


def _refill_heights():
    try:
        first = parse_heights(st.session_state[_k("He")])[0]
    except (ValueError, IndexError):
        first = 3.0
    st.session_state[_k("He")] = ",".join([str(first)] * int(st.session_state[_k("Ne")]))


def render_form():
    geo = section("geo", ":material/square_foot:", T("ui_web_geo"))
    g1, g2, g3, g4 = geo.columns(4)
    g1.number_input(T("ui_nx"), min_value=1, max_value=30, step=1, key=_k("Nx"))
    g2.number_input(T("ui_ny"), min_value=1, max_value=30, step=1, key=_k("Ny"))
    g3.number_input(T("ui_lx"), min_value=0.1, max_value=99.0, step=0.1, format="%.2f", key=_k("Lx"))
    g4.number_input(T("ui_ly"), min_value=0.1, max_value=99.0, step=0.1, format="%.2f", key=_k("Ly"))
    h1, h2, h3, h4 = geo.columns(4)
    h1.number_input(T("ui_ne"), min_value=1, max_value=50, step=1, key=_k("Ne"), on_change=_refill_heights)
    h2.text_input(T("ui_he"), key=_k("He"), placeholder="3.0,3.0")
    h3.number_input(T("ui_ep"), min_value=0.01, max_value=2.0, step=0.01, format="%.2f", key=_k("Ep"))
    choice(h4, "segmented", T("ui_type_appui"), APPUIS, _k("TypeAppui"), lambda v: T(f"appui_{v.lower()}"))
    geo.checkbox(T("ui_creer_systemes"), key=_k("creer_systemes"))


def preview(p):
    import plotly.graph_objects as go

    columns, beams, slabs, supports, _z = _geometry(p)

    def lines(segs, color, width):
        xs, ys, zs = [], [], []
        for a, b in segs:
            xs += [a[0], b[0], None]
            ys += [a[1], b[1], None]
            zs += [a[2], b[2], None]
        return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines",
                            line=dict(color=color, width=width), hoverinfo="skip")

    slab_edges = [(s["pts"][i], s["pts"][(i + 1) % 4]) for s in slabs for i in range(4)]
    fig = go.Figure([
        lines([(c["start"], c["end"]) for c in columns], "#4A7FE0", 5),
        lines([(b["start"], b["end"]) for b in beams], "#2CB67D", 3),
        lines(slab_edges, "#9AA4B2", 1),
        go.Scatter3d(x=[s[0] for s in supports], y=[s[1] for s in supports], z=[s[2] for s in supports],
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
                        eye=dict(x=1.6 / 0.7, y=-1.6 / 0.7, z=1.1 / 0.7)),
        ),
    )
    return fig


def validate(p):
    errors = []
    if int(p["Nx"]) < 1: errors.append(T("val_nx"))
    if int(p["Ny"]) < 1: errors.append(T("val_ny"))
    if int(p["Ne"]) < 1: errors.append(T("val_ne"))
    if float(p["Lx"]) <= 0: errors.append(T("val_lx"))
    if float(p["Ly"]) <= 0: errors.append(T("val_ly"))
    if float(p["Ep"]) <= 0: errors.append(T("val_ep"))
    if p["M"] not in MATERIALS: errors.append(T("val_materiau"))
    if p["TypeAppui"] not in APPUIS: errors.append(T("val_appui"))

    try:
        he = parse_heights(p["He"])
    except ValueError:
        raise ValueError(T("ui_he_invalid"))
    if len(he) not in (1, int(p["Ne"])):
        errors.append(T("val_he_count", n=int(p["Ne"])))
    elif any(not math.isfinite(h) or h <= 0 for h in he):
        errors.append(T("val_he"))

    for name in ELEMENTS:
        try:
            parse_section(p[name])
        except ValueError:
            errors.append(T("val_section", nom=p[name]))

    if not errors:
        he_min, ep = min(heights(p)), float(p["Ep"])
        for name in ("Sbr", "Sbi"):
            h = section_height(p[name])
            if h >= he_min:
                errors.append(T("val_poutre_h", nom=p[name], h=h, he=he_min))
            if ep >= h:
                errors.append(T("val_ep_h", ep=ep, nom=p[name], h=h))

    if errors:
        raise ValueError("\n".join(errors))


def build(host, p, log):
    columns, beams, slabs, supports, z = _geometry(p)
    ne, ep = int(p["Ne"]), float(p["Ep"])

    log(T("log_materiau", nom=p["M"]))
    mat_id = ad_api.create_material(host, p["M"])
    log(T("log_materiau_ok", nom=p["M"], eid=mat_id))

    log(T("log_sections"))
    sec = {name: ad_api.create_section(host, p[name]) for name in ELEMENTS}

    roots, systems = [], []
    if p["creer_systemes"]:
        log(T("log_systemes", n=ne + 1))
        for k in range(ne + 1):
            name = f"Étage {k + 1} - R+{k}"
            root = ad_api.create_system(host, name, parent_eid=0)
            roots.append((root, name))
            subs = (["APPUI"] if k == 0 else []) + SUB_SYSTEMS
            systems.append({s: [ad_api.create_system(host, s, parent_eid=root)] for s in subs})

    def sys_ids(level, sub):
        return systems[level][sub] if systems else None

    counts = {"poteaux_facade": 0, "poteaux_int": 0, "poutres_rive": 0, "poutres_int": 0, "dalles": 0, "appuis": 0}

    log(T("log_poteaux", n=len(columns)))
    for c in columns:
        ad_api.create_linear_element(host, c["start"], c["end"], mat_id, sec["Spf" if c["facade"] else "Spi"],
                                     user_name="Poteau façade" if c["facade"] else "Poteau intérieur",
                                     system_ids=sys_ids(c["level"], "POTEAU"))
        counts["poteaux_facade" if c["facade"] else "poteaux_int"] += 1

    log(T("log_appuis_n", n=len(supports)))
    for pt in supports:
        ad_api.create_support(host, pt, mat_id, p["TypeAppui"], user_name="Appui", system_ids=sys_ids(0, "APPUI"))
        counts["appuis"] += 1

    log(T("log_poutres", n=len(beams)))
    for b in beams:
        ad_api.create_linear_element(host, b["start"], b["end"], mat_id, sec["Sbr" if b["rive"] else "Sbi"],
                                     user_name="Poutre de rive" if b["rive"] else "Poutre intérieure",
                                     system_ids=sys_ids(b["level"], "POUTRE"), excentration=POUTRE_EXCENTRATION)
        counts["poutres_rive" if b["rive"] else "poutres_int"] += 1

    log(T("log_dalles", n=len(slabs)))
    for s in slabs:
        ad_api.create_planar_element(host, s["pts"], mat_id, ep, DALLE_EXCENTREMENT * ep,
                                     user_name="Dalle", system_ids=sys_ids(s["level"], "DALLE"))
        counts["dalles"] += 1

    if roots:
        log(T("log_niveaux"))
        for k, (eid, name) in enumerate(roots):
            ad_api.update_system_level(host, eid, name, k + 1, z[k], z[min(k + 1, ne)])

    def meters(v):
        return T("syn_unite_m", val=v)

    rows = [
        (T("syn_travees"), f"{p['Nx']} x {p['Ny']}"),
        (T("syn_entraxes"), f"{p['Lx']} m / {p['Ly']} m"),
        (T("syn_emprise"), f"{round(p['Nx'] * p['Lx'], 3)} m x {round(p['Ny'] * p['Ly'], 3)} m"),
        (T("syn_etages"), ne),
        (T("syn_hauteurs"), ", ".join(str(h) for h in heights(p)) + " m"),
        (T("syn_h_totale"), meters(z[-1])),
        (T("syn_poteaux_facade", nom=p["Spf"]), counts["poteaux_facade"]),
        (T("syn_poteaux_int", nom=p["Spi"]), counts["poteaux_int"]),
        (T("syn_poutres_rive", nom=p["Sbr"]), counts["poutres_rive"]),
        (T("syn_poutres_int", nom=p["Sbi"]), counts["poutres_int"]),
        (T("syn_dalles", ep=ep), counts["dalles"]),
        (T("syn_appui"), T(f"appui_{p['TypeAppui'].lower()}")),
        (T("syn_materiau"), p["M"]),
        (T("syn_appuis"), counts["appuis"]),
    ]
    if roots:
        rows.append((T("syn_systemes"), len(roots)))
    rows.append((T("syn_total"), sum(counts.values())))
    return rows

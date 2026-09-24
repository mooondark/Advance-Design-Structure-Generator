"""Portique metallique a deux versants avec pannes, parois et poids propre."""
import math

import streamlit as st

from core import ad_api
from core.i18n import T
from core.layout import section

KEY = "steel_frame"
TITLE_KEY = "structure_steel_frame"
ICON = ":material/foundation:"
DEFAULT_MATERIAL = "S275"
_MAIN = ["HEA", "HEB", "HEM", "IPE"]
ELEMENTS = {
    "Sp": ("ui_sec_poteaux",      _MAIN, "HEA400"),
    "Sa": ("ui_sec_arbaletriers", _MAIN, "IPE400"),
    "Sn": ("ui_sec_pannes",       ["IPE", "IPN", "UPN", "UPE", "HEA"], "IPE160"),
}
DEFAULTS = {
    "n": 5, "e": 5.0, "Hg": 6.0, "Hd": 4.0, "L": 18.0, "AR": 7.0, "F": 1.2,
    "TypeAppui": "HINGED",
    "Npg": 5, "Npd": 7, "Dbg": 0.3, "Dbd": 0.3,
    "creer_parois": True, "creer_systemes": True,
}
APPUIS = ["HINGED", "FIXED"]

RELAXATION_PANNES = {
    "startBoundaryConnection": {
        "relaxationTx": False, "relaxationTy": False, "relaxationTz": False,
        "relaxationRx": False, "relaxationRy": True,  "relaxationRz": True,
    },
    "endBoundaryConnection": {
        "relaxationTx": False, "relaxationTy": False, "relaxationTz": False,
        "relaxationRx": False, "relaxationRy": True,  "relaxationRz": True,
    },
}


def _k(name):
    return f"{KEY}.{name}"


def roof_quad_oriented(pt_a0, pt_b0, pt_b1, pt_a1, longitudinal_length, transverse_length):
    if longitudinal_length >= transverse_length:
        return [pt_a0, pt_a1, pt_b1, pt_b0]
    return [pt_a0, pt_b0, pt_b1, pt_a1]


def point_on_rafter(pt_base, pt_faitage, dist_from_base):
    dx = pt_faitage[0] - pt_base[0]
    dy = pt_faitage[1] - pt_base[1]
    dz = pt_faitage[2] - pt_base[2]
    length = math.sqrt(dx*dx + dy*dy + dz*dz)
    t = dist_from_base / length
    return (pt_base[0] + t*dx, pt_base[1] + t*dy, pt_base[2] + t*dz)


def _derive_geometry(p):
    Hg, Hd, L, AR, F = float(p["Hg"]), float(p["Hd"]), float(p["L"]), float(p["AR"]), float(p["F"])
    Npg, Npd = int(p["Npg"]), int(p["Npd"])
    Dbg, Dbd = float(p["Dbg"]), float(p["Dbd"])
    H_faitage = max(Hg, Hd) + F
    Lg = math.sqrt(AR ** 2 + (H_faitage - Hg) ** 2)
    Ld = math.sqrt((L - AR) ** 2 + (H_faitage - Hd) ** 2)
    pos_g = [k * (Lg - Dbg) / (Npg - 1) for k in range(Npg)] if Npg >= 2 else []
    pos_d = [k * (Ld - Dbd) / (Npd - 1) for k in range(Npd)] if Npd >= 2 else []
    return H_faitage, Lg, Ld, pos_g, pos_d


def render_form():
    geo = section("geo", ":material/square_foot:", T("ui_web_geo"))
    g1, g2, g3, g4 = geo.columns(4)
    g1.number_input(T("ui_nb_portiques"), min_value=2, max_value=25, step=1, key=_k("n"))
    g1.number_input(T("ui_portee"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("L"))
    g2.number_input(T("ui_entraxe"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("e"))
    g2.number_input(T("ui_ar"), min_value=0.01, max_value=999.0, step=0.1, format="%.2f", key=_k("AR"))
    g3.number_input(T("ui_hg"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("Hg"))
    g3.number_input(T("ui_fleche"), min_value=0.01, max_value=999.0, step=0.01, format="%.2f", key=_k("F"))
    g4.number_input(T("ui_hd"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("Hd"))
    g4.segmented_control(T("ui_type_appui"), options=APPUIS, format_func=lambda v: T(f"appui_{v.lower()}"),
                         key=_k("TypeAppui"), required=True)

    c1, c2 = geo.columns(2)
    c1.checkbox(T("ui_creer_parois"), key=_k("creer_parois"))
    c2.checkbox(T("ui_creer_systemes"), key=_k("creer_systemes"))

    p1, p2, p3, p4 = section("pannes", ":material/straighten:", T("ui_web_pannes")).columns(4)
    p1.number_input(T("ui_npg"), min_value=2, max_value=99, step=1, key=_k("Npg"))
    p2.number_input(T("ui_dbg"), min_value=0.0, max_value=999.0, step=0.05, format="%.2f", key=_k("Dbg"))
    p3.number_input(T("ui_npd"), min_value=2, max_value=99, step=1, key=_k("Npd"))
    p4.number_input(T("ui_dbd"), min_value=0.0, max_value=999.0, step=0.05, format="%.2f", key=_k("Dbd"))


def _wireframe_segments(p):
    n, e = int(p["n"]), float(p["e"])
    Hg, Hd, L, AR = float(p["Hg"]), float(p["Hd"]), float(p["L"]), float(p["AR"])
    H_faitage, Lg, Ld, pos_g, pos_d = _derive_geometry(p)
    if Lg <= 0 or Ld <= 0 or not pos_g or not pos_d or float(p["Dbg"]) >= Lg or float(p["Dbd"]) >= Ld:
        raise ValueError("geometrie invalide")

    portiques, pannes, supports = [], [], []
    for i in range(n):
        Yi = i * e
        pied_g, sommet_g = (0, Yi, 0), (0, Yi, Hg)
        pied_d, sommet_d = (L, Yi, 0), (L, Yi, Hd)
        faitage = (AR, Yi, H_faitage)
        portiques += [(pied_g, sommet_g), (pied_d, sommet_d), (sommet_g, faitage), (sommet_d, faitage)]
        supports += [pied_g, pied_d]

    for i in range(n - 1):
        Y0, Y1 = i * e, (i + 1) * e
        f0, f1 = (AR, Y0, H_faitage), (AR, Y1, H_faitage)
        for d in pos_g:
            pannes.append((point_on_rafter((0, Y0, Hg), f0, d), point_on_rafter((0, Y1, Hg), f1, d)))
        for d in pos_d:
            pannes.append((point_on_rafter((L, Y0, Hd), f0, d), point_on_rafter((L, Y1, Hd), f1, d)))

    return portiques, pannes, supports


def preview(p):
    import plotly.graph_objects as go

    portiques, pannes, supports = _wireframe_segments(p)

    def lines(segs, color, width):
        xs, ys, zs = [], [], []
        for a, b in segs:
            xs += [a[0], b[0], None]
            ys += [a[1], b[1], None]
            zs += [a[2], b[2], None]
        return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines",
                            line=dict(color=color, width=width), hoverinfo="skip")

    fig = go.Figure([
        lines(portiques, "#4A7FE0", 5),
        lines(pannes, "#2CB67D", 2),
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
    if not (2 <= p["n"] <= 25):   errors.append(T("val_n"))
    if p["e"] <= 0:               errors.append(T("val_e"))
    if p["Hg"] <= 0:              errors.append(T("val_Hg"))
    if p["Hd"] <= 0:              errors.append(T("val_Hd"))
    if p["L"] <= 0:               errors.append(T("val_L"))
    if not (0 < p["AR"] < p["L"]): errors.append(T("val_AR"))
    if p["F"] <= 0:               errors.append(T("val_F"))
    if p["TypeAppui"] not in APPUIS: errors.append(T("val_appui"))
    if p["Npg"] < 2:              errors.append(T("val_Npg"))
    if p["Npd"] < 2:              errors.append(T("val_Npd"))
    if p["Dbg"] < 0:              errors.append(T("val_Dbg"))
    if p["Dbd"] < 0:              errors.append(T("val_Dbd"))

    if not errors:
        _, Lg, Ld, _, _ = _derive_geometry(p)
        if p["Dbg"] >= Lg:
            errors.append(T("val_Dbg_long", dbg=p["Dbg"], lg=round(Lg, 3)))
        if p["Dbd"] >= Ld:
            errors.append(T("val_Dbd_long", dbd=p["Dbd"], ld=round(Ld, 3)))

    if errors:
        raise ValueError("\n".join(errors))


def build(host, p, log):
    n, e_val = p["n"], p["e"]
    Hg, Hd, L, AR = p["Hg"], p["Hd"], p["L"], p["AR"]
    type_appui    = p["TypeAppui"]
    creer_parois  = p["creer_parois"]
    creer_systemes = p["creer_systemes"]

    H_faitage, Lg, Ld, positions_g, positions_d = _derive_geometry(p)

    log(T("log_materiau", nom=p["M"]))
    mat_id = ad_api.create_material(host, p["M"])
    log(T("log_materiau_ok", nom=p["M"], eid=mat_id))

    log(T("log_sections"))
    sec_poteau = ad_api.create_section(host, p["Sp"])
    sec_arbal  = ad_api.create_section(host, p["Sa"])
    sec_panne  = ad_api.create_section(host, p["Sn"])
    log(T("log_sections_ok", Sp=p["Sp"], eid_p=sec_poteau,
             Sa=p["Sa"], eid_a=sec_arbal, Sn=p["Sn"], eid_n=sec_panne))

    log(T("log_cas_charge"))
    fam_g_eid, case_g_eid = ad_api.create_dead_load_case(
        host, T("ad_famille_g"), T("ad_cas_g"))
    log(T("log_cas_charge_ok", eid_fam=fam_g_eid, eid_cas=case_g_eid))

    counts = {"poteaux": 0, "arbaletriers": 0, "appuis": 0, "pannes_g": 0, "pannes_d": 0, "parois": 0}

    log(T("log_portiques", n=n))
    for i in range(n):
        Yi      = i * e_val
        pied_g  = (0, Yi, 0);  sommet_g = (0, Yi, Hg)
        pied_d  = (L, Yi, 0);  sommet_d = (L, Yi, Hd)
        faitage = (AR, Yi, H_faitage)

        portique_sys_ids = None
        appuis_sys_ids   = None
        if creer_systemes:
            portique_eid = ad_api.create_system(host, f"Portique {i+1}", parent_eid=0)
            appuis_eid   = ad_api.create_system(host, "Appuis", parent_eid=portique_eid)
            portique_sys_ids = [portique_eid]
            appuis_sys_ids   = [appuis_eid]

        ad_api.create_linear_element(host, pied_g, sommet_g, mat_id, sec_poteau, "bar",
                               user_name="Poteau Gauche", system_ids=portique_sys_ids)
        ad_api.create_linear_element(host, pied_d, sommet_d, mat_id, sec_poteau, "bar",
                               user_name="Poteau Droite", system_ids=portique_sys_ids)
        counts["poteaux"] += 2

        ad_api.create_linear_element(host, sommet_g, faitage, mat_id, sec_arbal,
                               user_name="Arbalétrier Gauche", system_ids=portique_sys_ids)
        ad_api.create_linear_element(host, sommet_d, faitage, mat_id, sec_arbal,
                               user_name="Arbalétrier Droite", system_ids=portique_sys_ids)
        counts["arbaletriers"] += 2

        ad_api.create_support(host, pied_g, mat_id, type_appui,
                        user_name="Appui Gauche", system_ids=appuis_sys_ids)
        ad_api.create_support(host, pied_d, mat_id, type_appui,
                        user_name="Appui Droite", system_ids=appuis_sys_ids)
        counts["appuis"] += 2

        log(T("log_portique_ok", i=i+1, n=n))

    pannes_sys_ids = None
    if creer_systemes:
        pannes_eid = ad_api.create_system(host, "Pannes", parent_eid=0)
        pannes_sys_ids = [pannes_eid]

    log(T("log_pannes_g"))
    for i in range(n - 1):
        Yi0, Yi1 = i * e_val, (i + 1) * e_val
        sg0 = (0, Yi0, Hg);  f0 = (AR, Yi0, H_faitage)
        sg1 = (0, Yi1, Hg);  f1 = (AR, Yi1, H_faitage)
        for dist in positions_g:
            ad_api.create_linear_element(
                host,
                point_on_rafter(sg0, f0, dist),
                point_on_rafter(sg1, f1, dist),
                mat_id, sec_panne, relaxation=RELAXATION_PANNES,
                user_name="Panne", system_ids=pannes_sys_ids,
            )
            counts["pannes_g"] += 1

    log(T("log_pannes_d"))
    for i in range(n - 1):
        Yi0, Yi1 = i * e_val, (i + 1) * e_val
        sd0 = (L, Yi0, Hd);  f0 = (AR, Yi0, H_faitage)
        sd1 = (L, Yi1, Hd);  f1 = (AR, Yi1, H_faitage)
        for dist in positions_d:
            ad_api.create_linear_element(
                host,
                point_on_rafter(sd0, f0, dist),
                point_on_rafter(sd1, f1, dist),
                mat_id, sec_panne, relaxation=RELAXATION_PANNES,
                user_name="Panne", system_ids=pannes_sys_ids,
            )
            counts["pannes_d"] += 1

    if creer_parois:
        log(T("log_parois"))
        Y0 = 0;  Yn = (n - 1) * e_val

        parois_sys_ids = None
        if creer_systemes:
            parois_eid = ad_api.create_system(host, "Parois", parent_eid=0)
            parois_sys_ids = [parois_eid]

        pied_g0  = (0, Y0, 0);  sommet_g0 = (0, Y0, Hg);  faitage0  = (AR, Y0, H_faitage)
        pied_d0  = (L, Y0, 0);  sommet_d0 = (L, Y0, Hd)
        pied_gN  = (0, Yn, 0);  sommet_gN = (0, Yn, Hg);  faitageN  = (AR, Yn, H_faitage)
        pied_dN  = (L, Yn, 0);  sommet_dN = (L, Yn, Hd)

        ad_api.create_load_area(host, [sommet_g0, faitage0, sommet_d0, pied_d0, pied_g0],
                         "Pignon_1er_portique", "eFloorDeckLoadSpanDirectionX",
                         user_name="Paroi", system_ids=parois_sys_ids)
        counts["parois"] += 1

        ad_api.create_load_area(host, [sommet_gN, faitageN, sommet_dN, pied_dN, pied_gN],
                         "Pignon_dernier_portique", "eFloorDeckLoadSpanDirectionX",
                         user_name="Paroi", system_ids=parois_sys_ids)
        counts["parois"] += 1

        ad_api.create_load_area(host, [pied_g0, pied_gN, sommet_gN, sommet_g0],
                         "Facade_poteaux_gauche", "eFloorDeckLoadSpanDirectionX",
                         user_name="Paroi", system_ids=parois_sys_ids)
        counts["parois"] += 1

        ad_api.create_load_area(host, [pied_d0, pied_dN, sommet_dN, sommet_d0],
                         "Facade_poteaux_droit", "eFloorDeckLoadSpanDirectionX",
                         user_name="Paroi", system_ids=parois_sys_ids)
        counts["parois"] += 1

        longueur_longitudinale = Yn - Y0
        pts_versant_g = roof_quad_oriented(sommet_g0, faitage0, faitageN, sommet_gN,
                                           longueur_longitudinale, Lg)
        ad_api.create_load_area(host, pts_versant_g, "Versant_arbaletriers_gauche",
                         "eFloorDeckLoadSpanDirectionY",
                         user_name="Paroi", system_ids=parois_sys_ids)
        counts["parois"] += 1

        pts_versant_d = roof_quad_oriented(faitage0, sommet_d0, sommet_dN, faitageN,
                                           longueur_longitudinale, Ld)
        ad_api.create_load_area(host, pts_versant_d, "Versant_arbaletriers_droit",
                         "eFloorDeckLoadSpanDirectionY",
                         user_name="Paroi", system_ids=parois_sys_ids)
        counts["parois"] += 1

        log(T("log_parois_ok", n=counts["parois"]))

    def meters(v):
        return T("syn_unite_m", val=v)

    rows = [
        (T("syn_portiques"), p["n"]),
        (T("syn_entraxe"), meters(p["e"])),
        (T("syn_hg_hd"), T("syn_unite_m_m", vg=p["Hg"], vd=p["Hd"])),
        (T("syn_portee"), meters(p["L"])),
        (T("syn_ar"), meters(p["AR"])),
        (T("syn_fleche"), meters(p["F"])),
        (T("syn_h_faitage"), meters(f"{H_faitage:.3f}")),
        (T("syn_lg"), meters(f"{Lg:.3f}")),
        (T("syn_ld"), meters(f"{Ld:.3f}")),
        (T("syn_appui"), T(f"appui_{p['TypeAppui'].lower()}")),
        (T("syn_poteaux", Sp=p["Sp"]), counts["poteaux"]),
        (T("syn_arbaletriers", Sa=p["Sa"]), counts["arbaletriers"]),
        (T("syn_pannes_g", Sn=p["Sn"]), counts["pannes_g"]),
        (T("syn_pannes_d", Sn=p["Sn"]), counts["pannes_d"]),
        (T("syn_appuis"), counts["appuis"]),
    ]
    if creer_parois:
        rows.append((T("syn_parois"), counts["parois"]))
    rows.append((T("syn_total"), sum(counts.values())))
    return rows


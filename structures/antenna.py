"""Pylone antenne treillis (base triangle ou carre) avec haubans optionnels."""
import math

import streamlit as st

from core import ad_api
from core.i18n import T
from core.layout import section

KEY = "antenna"
TITLE_KEY = "structure_antenna"
ICON = ":material/cell_tower:"
DEFAULT_MATERIAL = "S235"
_FAMILIES = ["CHSC", "CHSH", "RHSC", "RHSH", "SHSC", "SHSH", "L", "Li"]
ELEMENTS = {
    "section":     ("ui_section",     _FAMILIES, "CHS88.9x3C"),
    "section_guy": ("ui_section_guy", _FAMILIES, "CHS21.3x2C"),
}
DEFAULTS = {
    "height": 20.0,
    "base_type": "triangle",
    "num_levels": 20,
    "base_size": 0.5,
    "guy_levels": 0,
    "guy_heights": "",
    "anchor_distance": 2.0,
    "creer_systemes": True,
}
BASE_TYPES = ["triangle", "square"]


def _k(name):
    return f"{KEY}.{name}"


def validate_inputs(height: float, base_type: str, num_levels: int,
                    base_size: float, guy_levels: int, guy_heights: list,
                    anchor_distance: float) -> None:
    if not math.isfinite(height) or height <= 0:
        raise ValueError("HEIGHT must be a finite number > 0.")
    if base_type not in ['triangle', 'square']:
        raise ValueError("BASE_TYPE must be 'triangle' or 'square'.")
    if num_levels < 1:
        raise ValueError("NUM_LEVELS must be >= 1.")
    if not math.isfinite(base_size) or base_size <= 0:
        raise ValueError("BASE_SIZE must be a finite number > 0.")

    if guy_levels > 0:
        if len(guy_heights) != guy_levels:
            raise ValueError(f"GUY_HEIGHTS must contain exactly {guy_levels} values.")
        for h in guy_heights:
            if not math.isfinite(h) or h <= 0 or h > height:
                raise ValueError(f"All guy heights must be > 0 and <= {height}.")
        # Check ascending order
        for i in range(1, len(guy_heights)):
            if guy_heights[i] <= guy_heights[i-1]:
                raise ValueError("GUY_HEIGHTS must be in ascending order.")
        if not math.isfinite(anchor_distance) or anchor_distance <= 0:
            raise ValueError("ANCHOR_DISTANCE must be a finite number > 0 when guy wires are specified.")


def generate_antenna_tower(height: float, base_type: str, num_levels: int,
                           base_size: float, guy_levels: int = 0,
                           guy_heights: list = None,
                           anchor_distance: float = 0.0) -> dict:
    """
    Generate geometry payload for a parametric lattice antenna tower.

    Parameters:
        height         - total height of tower (m)
        base_type      - 'triangle' or 'square'
        num_levels     - number of horizontal levels
        base_size      - distance from center to legs (m)
        guy_levels     - number of guy wire attachment levels (0 = no guys)
        guy_heights    - list of heights where guys connect to tower (m)
        anchor_distance- distance from center to ground anchors (m)

    Returns a dict with metadata, nodes, elements, supports, guy_wires, and anchors.
    """
    if guy_heights is None:
        guy_heights = []

    validate_inputs(height, base_type, num_levels, base_size,
                   guy_levels, guy_heights, anchor_distance)

    num_legs = 3 if base_type == 'triangle' else 4
    level_height = height / num_levels

    # --- Generate tower nodes ---
    nodes = {}
    node_index = 0

    # Define leg angles
    if base_type == 'triangle':
        leg_angles = [90, 210, 330]  # degrees
    else:
        leg_angles = [45, 135, 225, 315]  # degrees

    # Create nodes for each level
    for level in range(num_levels + 1):
        z = round(level * level_height, 6)

        for leg_idx, angle in enumerate(leg_angles):
            angle_rad = math.radians(angle)
            x = round(base_size * math.cos(angle_rad), 6)
            y = round(base_size * math.sin(angle_rad), 6)

            node_name = f"N{node_index}"
            nodes[node_name] = {"x": x, "y": y, "z": z}
            node_index += 1

    # --- Generate tower elements ---
    elements = []
    elem_id = 1

    def node_at_level_leg(level: int, leg: int) -> str:
        return f"N{level * num_legs + leg}"

    # Vertical elements (legs)
    for level in range(num_levels):
        for leg in range(num_legs):
            sn = node_at_level_leg(level, leg)
            en = node_at_level_leg(level + 1, leg)
            elements.append({
                "id": elem_id,
                "type": "vertical",
                "start_node": sn,
                "end_node": en,
                "start": nodes[sn],
                "end": nodes[en]
            })
            elem_id += 1

    # Horizontal elements at each level (top of segment)
    for level in range(1, num_levels + 1):
        for leg in range(num_legs):
            sn = node_at_level_leg(level, leg)
            en = node_at_level_leg(level, (leg + 1) % num_legs)
            elements.append({
                "id": elem_id,
                "type": "horizontal",
                "start_node": sn,
                "end_node": en,
                "start": nodes[sn],
                "end": nodes[en]
            })
            elem_id += 1

    # Diagonal bracing (alternating pattern)
    for level in range(num_levels):
        for leg in range(num_legs):
            leg_bottom = node_at_level_leg(level, leg)
            leg_top = node_at_level_leg(level + 1, leg)
            next_leg_bottom = node_at_level_leg(level, (leg + 1) % num_legs)
            next_leg_top = node_at_level_leg(level + 1, (leg + 1) % num_legs)

            # Alternate diagonal direction based on level
            if level % 2 == 0:
                # / direction: bottom-left leg to top-right leg
                sn = leg_bottom
                en = next_leg_top
            else:
                # \ direction: bottom-right leg to top-left leg
                sn = next_leg_bottom
                en = leg_top

            elements.append({
                "id": elem_id,
                "type": "bracing",
                "start_node": sn,
                "end_node": en,
                "start": nodes[sn],
                "end": nodes[en]
            })
            elem_id += 1

    # --- Supports at base nodes (fixed) ---
    supports = []
    for leg in range(num_legs):
        node_name = node_at_level_leg(0, leg)
        supports.append({
            "node": node_name,
            "position": nodes[node_name],
            "type": "fixed",
            "Tx": True,
            "Ty": True,
            "Tz": True,
            "Rx": True,
            "Ry": True,
            "Rz": True
        })

    # --- Guy wires and anchors ---
    guy_wires = []
    anchors = []
    guy_id = 1
    anchor_id = 0

    if guy_levels > 0 and len(guy_heights) > 0:
        # Create anchor positions on ground
        for leg_idx, angle in enumerate(leg_angles):
            angle_rad = math.radians(angle)
            anchor_x = round(anchor_distance * math.cos(angle_rad), 6)
            anchor_y = round(anchor_distance * math.sin(angle_rad), 6)
            anchor_z = 0.0

            anchor_name = f"A{anchor_id}"
            nodes[anchor_name] = {"x": anchor_x, "y": anchor_y, "z": anchor_z}

            anchors.append({
                "id": anchor_name,
                "position": {"x": anchor_x, "y": anchor_y, "z": anchor_z},
                "type": "fixed",
                "Tx": True,
                "Ty": True,
                "Tz": True,
                "Rx": True,
                "Ry": True,
                "Rz": True
            })
            anchor_id += 1

        # Create guy wires from tower to anchors
        for guy_height in guy_heights:
            # Find the level closest to guy_height
            guy_level = round(guy_height / level_height)

            for leg in range(num_legs):
                tower_node = node_at_level_leg(guy_level, leg)
                anchor_node = f"A{leg}"

                guy_wires.append({
                    "id": guy_id,
                    "start_node": tower_node,
                    "end_node": anchor_node,
                    "start": nodes[tower_node],
                    "end": nodes[anchor_node]
                })
                guy_id += 1

    # --- Element counts ---
    element_counts = {
        "vertical": sum(1 for e in elements if e["type"] == "vertical"),
        "horizontal": sum(1 for e in elements if e["type"] == "horizontal"),
        "bracing": sum(1 for e in elements if e["type"] == "bracing"),
    }

    return {
        "metadata": {
            "description": "Antenna tower lattice structure geometry",
            "payload_type": "antenna-tower-definition",
            "payload_format": "JSON",
            "completion_required": True,
            "units": "m",
            "height": height,
            "base_type": base_type,
            "num_levels": num_levels,
            "base_size": base_size,
            "guy_levels": guy_levels,
            "guy_heights": guy_heights,
            "anchor_distance": anchor_distance,
            "element_counts": element_counts,
            "total_nodes": len(nodes),
            "total_elements": len(elements),
            "total_supports": len(supports),
            "total_guy_wires": len(guy_wires),
            "total_anchors": len(anchors),
        },
        "nodes": nodes,
        "elements": elements,
        "supports": supports,
        "guy_wires": guy_wires,
        "anchors": anchors
    }


def parse_heights(text):
    return [float(x) for x in (text or "").split(",") if x.strip()]


def _payload(p):
    return generate_antenna_tower(
        float(p["height"]), p["base_type"], int(p["num_levels"]), float(p["base_size"]),
        int(p["guy_levels"]), parse_heights(p["guy_heights"]), float(p["anchor_distance"]),
    )


def _refill_guy_heights():
    h = float(st.session_state[_k("height")])
    n = int(st.session_state[_k("guy_levels")])
    st.session_state[_k("guy_heights")] = ",".join(str(round(i * h / n, 2)) for i in range(1, n + 1)) if n > 0 else ""


def render_form():
    geo = section("geo", ":material/square_foot:", T("ui_web_geo"))
    g1, g2, g3, g4 = geo.columns(4)
    g1.number_input(T("ui_height"), min_value=0.1, max_value=999.0, step=0.5, format="%.2f",
                    key=_k("height"), on_change=_refill_guy_heights)
    g2.number_input(T("ui_num_levels"), min_value=1, max_value=200, step=1, key=_k("num_levels"))
    g3.number_input(T("ui_base_size"), min_value=0.01, max_value=99.0, step=0.05, format="%.2f",
                    key=_k("base_size"))
    g4.segmented_control(T("ui_base_type"), options=BASE_TYPES, format_func=lambda v: T(f"base_{v}"),
                         key=_k("base_type"), required=True)
    geo.checkbox(T("ui_creer_systemes"), key=_k("creer_systemes"))

    h1, h2, h3, _h4 = section("haubans", ":material/cable:", T("ui_web_haubans")).columns(4)
    h1.number_input(T("ui_guy_levels"), min_value=0, max_value=20, step=1,
                    key=_k("guy_levels"), on_change=_refill_guy_heights)
    h2.text_input(T("ui_guy_heights"), key=_k("guy_heights"), placeholder="20,40")
    h3.number_input(T("ui_anchor_distance"), min_value=0.0, max_value=999.0, step=0.5, format="%.2f",
                    key=_k("anchor_distance"))


def preview(p):
    import plotly.graph_objects as go

    payload = _payload(p)

    def seg(d):
        s, e = d["start"], d["end"]
        return ((s["x"], s["y"], s["z"]), (e["x"], e["y"], e["z"]))

    struct = [seg(el) for el in payload["elements"]]
    guys = [seg(g) for g in payload["guy_wires"]]
    markers = [(m["position"]["x"], m["position"]["y"], m["position"]["z"])
               for m in payload["supports"] + payload["anchors"]]

    def lines(segs, color, width):
        xs, ys, zs = [], [], []
        for a, b in segs:
            xs += [a[0], b[0], None]
            ys += [a[1], b[1], None]
            zs += [a[2], b[2], None]
        return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines",
                            line=dict(color=color, width=width), hoverinfo="skip")

    data = [lines(struct, "#4A7FE0", 3), lines(guys, "#E8A840", 1), go.Scatter3d(
        x=[m[0] for m in markers], y=[m[1] for m in markers], z=[m[2] for m in markers],
        mode="markers", hoverinfo="skip", marker=dict(size=3, color="#2CB67D", symbol="diamond"),
    )]
    # Ratio d'aspect normalise : aspectmode="data" place la camera dans un pylone tres haut.
    pts = [q for s in struct + guys for q in s] + markers
    spans = [(max(c) - min(c)) or 1.0 for c in zip(*pts)]
    m = max(spans)
    zoom = 1.90
    fig = go.Figure(data)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            aspectmode="manual",
            aspectratio=dict(x=spans[0] / m, y=spans[1] / m, z=spans[2] / m),
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            camera=dict(projection=dict(type="perspective"),
                        eye=dict(x=1.6 / zoom, y=-1.6 / zoom, z=1.1 / zoom)),
        ),
    )
    return fig


def validate(p):
    errors = []
    if float(p["height"]) <= 0:
        errors.append(T("val_height"))
    if p["base_type"] not in BASE_TYPES:
        errors.append(T("val_base_type"))
    if int(p["num_levels"]) < 1:
        errors.append(T("val_num_levels"))
    if float(p["base_size"]) <= 0:
        errors.append(T("val_base_size"))

    # Parse meme sans haubans : build() parse toujours le champ.
    try:
        gh = parse_heights(p["guy_heights"])
    except ValueError:
        raise ValueError(T("ui_guy_heights_invalid"))
    gl = int(p["guy_levels"])
    if gl > 0:
        if len(gh) != gl:
            errors.append(T("val_guy_count", n=gl))
        else:
            if any(not math.isfinite(h) or h <= 0 or h > float(p["height"]) for h in gh):
                errors.append(T("val_guy_range", h=p["height"]))
            if any(gh[i] <= gh[i - 1] for i in range(1, len(gh))):
                errors.append(T("val_guy_order"))
        if float(p["anchor_distance"]) <= 0:
            errors.append(T("val_anchor_distance"))

    if errors:
        raise ValueError("\n".join(errors))


def build(host, p, log):
    payload = _payload(p)

    log(T("log_materiau", nom=p["M"]))
    mat_id = ad_api.create_material(host, p["M"])
    log(T("log_materiau_ok", nom=p["M"], eid=mat_id))

    log(T("log_section", nom=p["section"]))
    sec_id = ad_api.create_section(host, p["section"])
    log(T("log_section_ok", nom=p["section"], eid=sec_id))

    sys_struct = sys_guy = sys_appui = None
    if p["creer_systemes"]:
        root = ad_api.create_system(host, "Pylone", parent_eid=0)
        sys_struct = [ad_api.create_system(host, "Structure", parent_eid=root)]
        sys_appui = [ad_api.create_system(host, "Appuis", parent_eid=root)]
        if payload["guy_wires"]:
            sys_guy = [ad_api.create_system(host, "Haubans", parent_eid=root)]

    counts = {"vertical": 0, "horizontal": 0, "bracing": 0, "guy_wires": 0, "supports": 0, "anchors": 0}

    def pt(d):
        return (d["x"], d["y"], d["z"])

    log(T("log_elements", n=len(payload["elements"])))
    for el in payload["elements"]:
        ad_api.create_linear_element(host, pt(el["start"]), pt(el["end"]), mat_id, sec_id,
                                     user_name=el["type"], system_ids=sys_struct)
        counts[el["type"]] += 1

    if payload["guy_wires"]:
        log(T("log_section", nom=p["section_guy"]))
        sec_guy_id = ad_api.create_section(host, p["section_guy"])
        log(T("log_section_ok", nom=p["section_guy"], eid=sec_guy_id))
        log(T("log_haubans", n=len(payload["guy_wires"])))
        for gw in payload["guy_wires"]:
            ad_api.create_linear_element(host, pt(gw["start"]), pt(gw["end"]), mat_id, sec_guy_id,
                                         beam_type="tie", user_name="Hauban", system_ids=sys_guy)
            counts["guy_wires"] += 1

    log(T("log_appuis"))
    for sup in payload["supports"]:
        ad_api.create_support(host, pt(sup["position"]), mat_id, "FIXED", user_name="Appui", system_ids=sys_appui)
        counts["supports"] += 1
    for anc in payload["anchors"]:
        ad_api.create_support(host, pt(anc["position"]), mat_id, "FIXED", user_name="Ancrage", system_ids=sys_guy)
        counts["anchors"] += 1

    def meters(v):
        return T("syn_unite_m", val=v)

    rows = [
        (T("syn_height"), meters(p["height"])),
        (T("syn_base_type"), T(f"base_{p['base_type']}")),
        (T("syn_num_levels"), p["num_levels"]),
        (T("syn_base_size"), meters(p["base_size"])),
    ]
    if counts["guy_wires"]:
        rows += [
            (T("syn_guy_levels"), p["guy_levels"]),
            (T("syn_guy_heights"), p["guy_heights"]),
            (T("syn_anchor_distance"), meters(p["anchor_distance"])),
        ]
    rows.append((T("syn_section", nom=p["section"]), counts["vertical"] + counts["horizontal"] + counts["bracing"]))
    if counts["guy_wires"]:
        rows.append((T("syn_section_guy", nom=p["section_guy"]), counts["guy_wires"]))
    rows += [
        (T("syn_vertical"), counts["vertical"]),
        (T("syn_horizontal"), counts["horizontal"]),
        (T("syn_bracing"), counts["bracing"]),
    ]
    if counts["guy_wires"]:
        rows.append((T("syn_haubans"), counts["guy_wires"]))
    rows.append((T("syn_appuis"), counts["supports"]))
    if counts["anchors"]:
        rows.append((T("syn_anchors"), counts["anchors"]))
    rows.append((T("syn_total"), sum(counts.values())))
    return rows

"""
Client HTTP pour l'API REST Advance Design (Graitec).
Aucune dependance Streamlit ni i18n. Reference des commandes : API Data/swagger.json.
"""

import socket
import urllib.parse

import requests

# Session HTTP réutilisée : keep-alive + pooling de connexions.
# Évite un handshake TCP par requête (des centaines lors d'une génération).
_SESSION = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=8)
_SESSION.mount("http://", _adapter)
_SESSION.mount("https://", _adapter)

STEEL_PROPS = {
    "S235": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 235_000},
    "S275": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 275_000},
    "S355": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 355_000},
    "S450": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 450_000},
    "S460": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 460_000},
}
MATERIALS = list(STEEL_PROPS)


def check_port(host: str) -> None:
    parsed   = urllib.parse.urlparse(host)
    hostname = parsed.hostname
    port     = parsed.port
    if hostname is None:
        raise ValueError(f"URL invalide : {host}")
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    try:
        # create_connection essaie toutes les adresses getaddrinfo (IPv4 + IPv6)
        socket.create_connection((hostname, port), timeout=3).close()
    except OSError as e:
        raise ConnectionError(f"Port inaccessible : {hostname}:{port}") from e


def _check(response: requests.Response, label: str) -> dict:
    try:
        data = response.json()
    except ValueError:
        data = None

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        body = data if data is not None else response.text[:500]
        raise RuntimeError(f"[{label}] HTTP {response.status_code} — {body}") from e

    if data is None:
        raise RuntimeError(f"[{label}] Réponse non-JSON — {response.text[:500]}")
    details = data.get("details", {})
    if not details.get("success", True):
        messages = "; ".join(d.get("message", "") for d in details.get("diagnostics", []))
        raise RuntimeError(f"[{label}] Erreur API — {messages}")
    return data


def new_project(host, fto_path):
    resp = _SESSION.post(
        f"{host}/api/Model/management/NewProject",
        params={"filename": fto_path}, json={}, timeout=30
    )
    _check(resp, "NewProject")


def open_project(host, fto_path):
    resp = _SESSION.post(
        f"{host}/api/Model/management/OpenProject",
        params={"filename": fto_path}, json={}, timeout=30
    )
    _check(resp, "OpenProject")


def close_project(host):
    try:
        _SESSION.post(f"{host}/api/Model/management/CloseProject", json={}, timeout=15)
    except Exception:
        pass


def create_material(host, name):
    props = STEEL_PROPS[name]
    data  = _check(
        _SESSION.post(f"{host}/api/Model/materials/CreateMaterial",
                      json={"$type": "MaterialSteel", "name": name, **props}),
        "CreateMaterial"
    )
    return data["data"]["value"]


def create_section(host, section_name):
    data = _check(
        _SESSION.post(f"{host}/api/Model/sections/CreateSection",
                      params={"sectionName": section_name}),
        f"CreateSection({section_name})"
    )
    return data["data"]["value"]


def create_linear_element(host, pt_start, pt_end, mat_id, sec_id,
                           beam_type="beamWStandardBending", relaxation=None,
                           user_name=None, system_ids=None):
    payload = {
        "$type":          "ElementLinear",
        "geomPtStart":    {"x": pt_start[0], "y": pt_start[1], "z": pt_start[2]},
        "geomPtEnd":      {"x": pt_end[0],   "y": pt_end[1],   "z": pt_end[2]},
        "material":       {"value": mat_id},
        "section":        {"value": sec_id},
        "linearElementType": "eLinearElementFEMTypeGeneral",
        "generalBeamType":   beam_type,
    }
    if relaxation is not None:
        payload["relaxationTotale"] = relaxation
    if user_name is not None:
        payload["userName"] = user_name
    if system_ids is not None:
        payload["systemIDs"] = [{"value": eid} for eid in system_ids]
    data = _check(
        _SESSION.post(f"{host}/api/Model/elements/CreateElement", json=payload),
        "CreateElement(linear)"
    )
    return data["data"]["value"]


def create_support(host, pt, mat_id, type_appui, user_name=None, system_ids=None):
    if type_appui == "FIXED":
        restraints = {"tx": True, "ty": True, "tz": True, "rx": True,  "ry": True,  "rz": True}
    else:
        restraints = {"tx": True, "ty": True, "tz": True, "rx": False, "ry": False, "rz": False}
    payload = {
        "$type":           "ElementRigidPunctualSupport",
        "geomPt":          {"x": pt[0], "y": pt[1], "z": pt[2]},
        "material":        {"value": mat_id},
        "constraintsType": "other",
        "restraints":      restraints,
    }
    if user_name is not None:
        payload["userName"] = user_name
    if system_ids is not None:
        payload["systemIDs"] = [{"value": eid} for eid in system_ids]
    data = _check(
        _SESSION.post(f"{host}/api/Model/elements/CreateElement", json=payload),
        f"CreateSupport({type_appui})"
    )
    return data["data"]["value"]


def create_system(host, name, parent_eid=0):
    data = _check(
        _SESSION.post(f"{host}/api/Model/elements/CreateInformationalElement",
                      json={"$type": "StructuralSystem", "userName": name,
                            "parentID": {"value": parent_eid}}),
        f"CreateSystem({name})"
    )
    return data["data"]["value"]


def create_dead_load_case(host, famille_name, cas_name):
    fam_data = _check(
        _SESSION.post(f"{host}/api/Model/elements/CreateInformationalElement",
                      json={"$type": "LoadCaseFamily_DeadLoads", "name": famille_name}),
        "CreateFamily(G)"
    )
    fam_eid  = fam_data["data"]["value"]
    case_data = _check(
        _SESSION.post(
            f"{host}/api/Model/elements/CreateInformationalElement",
            json={
                "$type":             "LoadCase_DeadLoads",
                "name":              cas_name,
                "loadCaseFamilyID":  {"value": fam_eid},
                "field":             {"x": 0.0, "y": 0.0, "z": -1.0},
            },
        ),
        "CreateCase(G1)"
    )
    case_eid = case_data["data"]["value"]
    return fam_eid, case_eid


def create_load_area(host, pts_list, label="LoadArea", span_direction=None,
                      user_name=None, system_ids=None):
    payload = {
        "$type":       "ElementLoadArea",
        "geomPtsList": [{"x": p[0], "y": p[1], "z": p[2]} for p in pts_list],
    }
    if span_direction:
        payload["loadTransferProperties"] = {
            "loadTransferMethodType":         "eLoadTransferMethodAuto",
            "loadTransferSpanDirectionType":  span_direction,
        }
    if user_name is not None:
        payload["userName"] = user_name
    if system_ids is not None:
        payload["systemIDs"] = [{"value": eid} for eid in system_ids]
    data = _check(
        _SESSION.post(f"{host}/api/Model/elements/CreateElement", json=payload),
        f"CreateLoadArea({label})"
    )
    return data["data"]["value"]

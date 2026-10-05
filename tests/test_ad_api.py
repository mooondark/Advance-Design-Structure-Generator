from core import ad_api


class _Resp:
    status_code = 200
    text = ""

    def json(self):
        return {"data": {"value": 7}, "details": {"success": True}}

    def raise_for_status(self):
        pass


def _capture(monkeypatch):
    calls = []

    def post(url, params=None, json=None, timeout=None):
        calls.append({"url": url, "params": params, "json": json})
        return _Resp()

    monkeypatch.setattr(ad_api._SESSION, "post", post)
    return calls


def test_grades():
    assert ad_api.STEEL_GRADES == ["S235", "S275", "S355", "S450", "S460"]
    assert ad_api.STEEL_PROPS["S460"]["sigmaE"] == 460_000
    assert list(ad_api.CONCRETE_PROPS) == ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50"]
    assert ad_api.CONCRETE_PROPS["C30/37"]["fck"] == 30_000


def test_create_material_steel_and_concrete(monkeypatch):
    calls = _capture(monkeypatch)
    ad_api.create_material("http://h", "S355")
    ad_api.create_material("http://h", "C25/30")
    assert calls[0]["json"]["$type"] == "MaterialSteel"
    assert calls[1]["json"]["$type"] == "MaterialReinforcedConcrete"
    assert calls[1]["json"]["name"] == "C25/30"
    assert calls[1]["json"]["fck"] == 25_000


def test_linear_excentration(monkeypatch):
    calls = _capture(monkeypatch)
    ad_api.create_linear_element("http://h", (0, 0, 3), (5, 0, 3), 1, 2)
    ad_api.create_linear_element("http://h", (0, 0, 3), (5, 0, 3), 1, 2, excentration="centre_haut")
    assert "sectionExcentration" not in calls[0]["json"]
    exc = calls[1]["json"]["sectionExcentration"]
    assert exc["option"] == "centre_haut" and exc["consideredInFEM"] is True


def test_planar_element(monkeypatch):
    calls = _capture(monkeypatch)
    eid = ad_api.create_planar_element("http://h", [(0, 0, 3), (5, 0, 3), (5, 5, 3)], 1, 0.2, -0.1,
                                       user_name="Dalle", system_ids=[9])
    body = calls[0]["json"]
    assert eid == 7
    assert calls[0]["url"].endswith("/api/Model/elements/CreateElement")
    assert body["$type"] == "ElementPlanar"
    assert body["geomPtsList"][2] == {"x": 5, "y": 5, "z": 3}
    assert body["thicknessIn1stVertex"] == 0.2 and body["eccentricity"] == -0.1
    assert body["userName"] == "Dalle" and body["systemIDs"] == [{"value": 9}]


def test_update_system_level(monkeypatch):
    calls = _capture(monkeypatch)
    ad_api.update_system_level("http://h", 42, "Étage 1 - R+0", 1, 0.0, 3.0)
    assert calls[0]["url"].endswith("/api/Model/elements/UpdateInformationalElement")
    assert calls[0]["params"] == {"elementId": 42}
    body = calls[0]["json"]
    assert body["$type"] == "StructuralSystem" and body["isLevel"] is True
    assert (body["levelNumber"], body["levelBottom"], body["levelTop"]) == (1, 0.0, 3.0)


def test_create_material_rigid(monkeypatch):
    calls = _capture(monkeypatch)
    assert ad_api.create_material("http://h", "Rigid") == 7
    assert calls[0]["json"] == {"$type": "MaterialRigid", "name": "Rigid"}

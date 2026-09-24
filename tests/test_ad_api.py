from core import ad_api


def test_materials():
    assert ad_api.MATERIALS == ["S235", "S275", "S355", "S450", "S460"]
    assert ad_api.STEEL_PROPS["S460"]["sigmaE"] == 460_000

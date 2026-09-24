# Structure Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fusionner SteelFrameGenerator et Antenna Generator en une application Streamlit unique, extensible par modules de structure.

**Architecture:** `app.py` compose la page ; `core/` contient le code partage (client API, profils, config, i18n, UI commune, orchestration) ; `structures/` contient un module par structure respectant un contrat fixe, reference dans un registre. L'etat de session est prefixe par structure et preserve du nettoyage des widgets Streamlit.

**Tech Stack:** Python 3.14, Streamlit 1.64, Plotly 7, requests, pytest 9 (`streamlit.testing.v1.AppTest` pour les tests d'interface).

**Spec:** `docs/superpowers/specs/2026-09-24-structure-generator-design.md`

## Global Constraints

- Materiaux : S235, S275, S355, S450, S460.
- Portique : `Sp` et `Sa` dans HEA, HEB, HEM, IPE ; `Sn` dans IPE, IPN, UPN, UPE, HEA ; defauts HEA400 / IPE400 / IPE160 ; materiau S275.
- Antenne : `section` et `section_guy` dans CHSC, CHSH, RHSC, RHSH, SHSC, SHSH, L, Li ; defauts CHS88.9x3C / CHS21.3x2C ; materiau S235.
- `AD_Profiles.md` et `API Data/` ne sont ni versionnes ni lus a l'execution ; seul `core/profiles.py` (genere) l'est.
- `config.ini` : section `[General]`, cles `language`, `api_server_exe`, `structure`.
- `T(key)` : section de la structure active, puis `[common]`, sinon `[key]`. Aucun repli `T(...) or "texte"`.
- Aucune dependance nouvelle : streamlit, requests, plotly seulement (pytest en dev).
- Pas d'em dash ni de guillemets typographiques dans le code ajoute ; les textes existants des fichiers de langue sont repris tels quels.
- Hauteur d'apercu unique : `PREVIEW_HEIGHT = 600` dans `core/ui.py`.
- Version : `VERSION = "2.0"` dans `app.py` ; `CHANGELOG.md` a la racine.
- Toutes les commandes sont lancees depuis la racine `E:\Git Repositories\Structure Generator`.
- `Originals/` n'est jamais modifie ni importe.

## Review Focus

- Passer de Portique a Antenne puis revenir : les valeurs saisies sont conservees (test AppTest, Task 9).
- Changer de famille de profil : le profil passe au premier de la nouvelle famille, sans exception Streamlit (test AppTest, Task 9).
- `config.ini` contient une structure inconnue (module retire) : l'application demarre sur la premiere structure du registre (test AppTest, Task 9).
- Hauteurs de haubans mal saisies (`"abc"`, `"20;40"`) : message de validation traduit, pas de trace Python ; l'apercu affiche le message d'indisponibilite (test, Task 5).
- Cle de traduction absente ou fichier de langue manquant : `[cle]` affiche, pas de plantage (test, Task 3).

---

## File Structure

| Fichier | Responsabilite |
|---|---|
| `pytest.ini` | `pythonpath = .`, `testpaths = tests` |
| `core/__init__.py` | vide |
| `core/ad_api.py` | client HTTP Advance Design, `STEEL_PROPS`, `MATERIALS` |
| `core/profiles.py` | `PROFILES = {famille: [noms]}` genere |
| `core/config.py` | `get_app_dir`, `CONFIG_FILE`, `load_config`, `save_config` |
| `core/i18n.py` | `LANG_LABELS`, `load_language`, `set_scope`, `T` |
| `core/runner.py` | `run_generation(structure, p, host, log)` |
| `core/ui.py` | CSS, etat de session, panneaux communs, apercu, journal |
| `structures/__init__.py` | `STRUCTURES` |
| `structures/antenna.py` | geometrie pylone + contrat |
| `structures/steel_frame.py` | geometrie portique + contrat |
| `tools/gen_profiles.py` | regenere `core/profiles.py` |
| `lang/fr.ini`, `lang/en.ini`, `lang/pl.ini` | traductions `[common]`, `[steel_frame]`, `[antenna]` |
| `app.py` | page Streamlit + lanceur PyInstaller |
| `start.bat`, `CHANGELOG.md` | livraison |
| `tests/test_*.py` | un fichier par module |

---

### Task 1: Client API et configuration pytest

**Files:**
- Create: `pytest.ini`, `core/__init__.py`, `core/ad_api.py`
- Test: `tests/test_ad_api.py`

**Interfaces:**
- Produces: `core.ad_api` avec `STEEL_PROPS: dict`, `MATERIALS: list[str]`, `check_port(host)`, `new_project(host, fto)`, `open_project(host, fto)`, `close_project(host)`, `create_material(host, name) -> int`, `create_section(host, name) -> int`, `create_linear_element(host, pt_start, pt_end, mat_id, sec_id, beam_type="beamWStandardBending", relaxation=None, user_name=None, system_ids=None) -> int`, `create_support(host, pt, mat_id, type_appui, user_name=None, system_ids=None) -> int`, `create_system(host, name, parent_eid=0) -> int`, `create_dead_load_case(host, famille_name, cas_name) -> (int, int)`, `create_load_area(host, pts_list, label="LoadArea", span_direction=None, user_name=None, system_ids=None) -> int`.

- [ ] **Step 1: Creer `pytest.ini`**

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 2: Ecrire le test**

`tests/test_ad_api.py` :

```python
from core import ad_api


def test_materials():
    assert ad_api.MATERIALS == ["S235", "S275", "S355", "S450", "S460"]
    assert ad_api.STEEL_PROPS["S460"]["sigmaE"] == 460_000
```

- [ ] **Step 3: Lancer le test, il echoue**

Run: `python -m pytest tests/test_ad_api.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'core'`

- [ ] **Step 4: Creer le module**

```bash
mkdir -p core tests
: > core/__init__.py
cp Originals/SteelFrameGenerator/advance_design_api.py core/ad_api.py
```

Dans `core/ad_api.py`, remplacer le docstring d'en-tete par :

```python
"""
Client HTTP pour l'API REST Advance Design (Graitec).
Aucune dependance Streamlit ni i18n. Reference des commandes : API Data/swagger.json.
"""
```

et remplacer le bloc `STEEL_PROPS` par :

```python
STEEL_PROPS = {
    "S235": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 235_000},
    "S275": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 275_000},
    "S355": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 355_000},
    "S450": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 450_000},
    "S460": {"e": 210_000_000, "ro": 7850, "nu": 0.3, "damping": 0.02, "alpha": 1.2e-5, "sigmaE": 460_000},
}
MATERIALS = list(STEEL_PROPS)
```

- [ ] **Step 5: Lancer le test, il passe**

Run: `python -m pytest tests/test_ad_api.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pytest.ini core/__init__.py core/ad_api.py tests/test_ad_api.py
git commit -m "feat: client API Advance Design partage, materiaux S450/S460"
```

---

### Task 2: Catalogue des profils

**Files:**
- Create: `tools/gen_profiles.py`, `core/profiles.py` (genere)
- Test: `tests/test_profiles.py`

**Interfaces:**
- Produces: `tools.gen_profiles.parse(text: str) -> dict[str, list[str]]`, `core.profiles.PROFILES: dict[str, list[str]]` (ordre des familles et des profils = ordre de `AD_Profiles.md`).

- [ ] **Step 1: Ecrire les tests**

`tests/test_profiles.py` :

```python
from core.profiles import PROFILES
from tools.gen_profiles import parse

SAMPLE = """# Titre

## Famille HEA

**Code famille :** HEA

| name | h | b |
|---|---|---|
| HEA100 | 96 | 100 |
| HEA120 | 114 | 120 |

## Famille HP (US)

| name | h |
|---|---|
| HP8x36 | 204 |
"""


def test_parse_sample():
    assert parse(SAMPLE) == {"HEA": ["HEA100", "HEA120"], "HP (US)": ["HP8x36"]}


def test_generated_module():
    assert len(PROFILES) == 35
    assert "HEA400" in PROFILES["HEA"]
    assert "CHS88.9x3C" in PROFILES["CHSC"]
    assert all(PROFILES.values())
```

- [ ] **Step 2: Lancer les tests, ils echouent**

Run: `python -m pytest tests/test_profiles.py -v`
Expected: FAIL, `ModuleNotFoundError`

- [ ] **Step 3: Ecrire `tools/gen_profiles.py`**

```python
"""Regenere core/profiles.py depuis AD_Profiles.md (usage developpeur, fichier non distribue)."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse(text):
    families, current = {}, None
    for line in text.splitlines():
        m = re.match(r"## Famille (.+)", line)
        if m:
            current = families.setdefault(m.group(1).strip(), [])
        elif current is not None and line.startswith("| "):
            name = line.split("|")[1].strip()
            if name != "name":
                current.append(name)
    return families


def main(src=os.path.join(ROOT, "AD_Profiles.md"), dst=os.path.join(ROOT, "core", "profiles.py")):
    with open(src, encoding="utf-8") as f:
        families = parse(f.read())
    lines = [
        '"""Catalogue des profils Advance Design (noms uniquement).',
        'Genere par tools/gen_profiles.py depuis AD_Profiles.md : ne pas editer a la main."""',
        "",
        "PROFILES = {",
    ]
    lines += [f"    {fam!r}: {names!r}," for fam, names in families.items()]
    lines.append("}")
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(families)} familles, {sum(map(len, families.values()))} profils -> {dst}")


if __name__ == "__main__":
    main()
```

Et `tools/__init__.py` vide (pour l'import dans les tests).

- [ ] **Step 4: Generer le module**

Run: `python tools/gen_profiles.py`
Expected: `35 familles, <N> profils -> ...core\profiles.py`

- [ ] **Step 5: Lancer les tests, ils passent**

Run: `python -m pytest tests/test_profiles.py -v`
Expected: 2 PASS

- [ ] **Step 6: Commit**

```bash
git add tools/__init__.py tools/gen_profiles.py core/profiles.py tests/test_profiles.py
git commit -m "feat: catalogue des profils genere depuis AD_Profiles.md"
```

---

### Task 3: Configuration et i18n

**Files:**
- Create: `core/config.py`, `core/i18n.py`
- Test: `tests/test_config.py`, `tests/test_i18n.py`

**Interfaces:**
- Produces: `core.config.get_app_dir() -> str` (racine du projet, ou dossier de l'exe en mode PyInstaller), `core.config.CONFIG_FILE: str`, `core.config.DEFAULTS: dict`, `core.config.load_config() -> dict` (cles `language`, `api_server_exe`, `structure`), `core.config.save_config(**values) -> None` (fusion avec l'existant).
- Produces: `core.i18n.DEFAULT_LANG = "fr"`, `core.i18n.LANG_LABELS: dict`, `core.i18n.load_language(code, lang_dir=None)`, `core.i18n.set_scope(name)`, `core.i18n.T(key, **kw) -> str`.

- [ ] **Step 1: Ecrire les tests**

`tests/conftest.py` (l'etat de `core.i18n` est global : sans ce reset, un test qui charge une vraie langue, comme les tests AppTest, changerait les messages vus par les tests suivants) :

```python
import pytest

from core import i18n


@pytest.fixture(autouse=True)
def _no_translations(tmp_path):
    i18n.load_language("fr", lang_dir=str(tmp_path))
    i18n.set_scope("common")
```

`tests/test_config.py` :

```python
from core import config


def test_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "config.ini"))
    assert config.load_config() == config.DEFAULTS


def test_save_merges(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_FILE", str(tmp_path / "config.ini"))
    config.save_config(language="en")
    config.save_config(structure="antenna")
    cfg = config.load_config()
    assert cfg["language"] == "en"
    assert cfg["structure"] == "antenna"
    assert cfg["api_server_exe"] == config.DEFAULTS["api_server_exe"]


def test_corrupted_file(tmp_path, monkeypatch):
    path = tmp_path / "config.ini"
    path.write_text("pas un ini", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_FILE", str(path))
    assert config.load_config() == config.DEFAULTS
```

`tests/test_i18n.py` :

```python
from core import i18n

INI = """[common]
a = A commun
x = X commun
fmt = Bonjour {nom}
multi = ligne1\\nligne2

[antenna]
x = X antenne
"""


def _load(tmp_path):
    (tmp_path / "fr.ini").write_text(INI, encoding="utf-8")
    i18n.load_language("fr", lang_dir=str(tmp_path))


def test_scope_then_common(tmp_path):
    _load(tmp_path)
    i18n.set_scope("antenna")
    assert i18n.T("x") == "X antenne"
    assert i18n.T("a") == "A commun"
    i18n.set_scope("steel_frame")
    assert i18n.T("x") == "X commun"


def test_format_and_newline(tmp_path):
    _load(tmp_path)
    assert i18n.T("fmt", nom="Bob") == "Bonjour Bob"
    assert i18n.T("multi") == "ligne1\nligne2"


def test_missing_key_and_file(tmp_path):
    _load(tmp_path)
    assert i18n.T("absente", n=1) == "[absente]"
    i18n.load_language("pl", lang_dir=str(tmp_path))
    assert i18n.T("a") == "[a]"
```

- [ ] **Step 2: Lancer les tests, ils echouent**

Run: `python -m pytest tests/test_config.py tests/test_i18n.py -v`
Expected: FAIL, `ImportError`

- [ ] **Step 3: Ecrire `core/config.py`**

```python
import configparser
import os
import sys

DEFAULTS = {
    "language": "fr",
    "api_server_exe": r"C:\Program Files\Graitec\Advance Design\2027\Bin\AD.API.Srv.exe",
    "structure": "steel_frame",
}


def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_FILE = os.path.join(get_app_dir(), "config.ini")


def load_config():
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(CONFIG_FILE, encoding="utf-8")
    except configparser.Error:
        return dict(DEFAULTS)
    section = parser["General"] if parser.has_section("General") else {}
    return {k: section.get(k, v) for k, v in DEFAULTS.items()}


def save_config(**values):
    cfg = load_config()
    cfg.update(values)
    parser = configparser.ConfigParser(interpolation=None)
    parser["General"] = cfg
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            parser.write(f)
    except OSError:
        pass
```

- [ ] **Step 4: Ecrire `core/i18n.py`**

```python
import configparser
import os

from core.config import get_app_dir

DEFAULT_LANG = "fr"
LANG_FILES = {"fr": "fr.ini", "en": "en.ini", "pl": "pl.ini"}
LANG_LABELS = {"fr": "Français", "en": "English", "pl": "Polski"}

_parser = configparser.ConfigParser(interpolation=None)
_scope = "common"


def load_language(code, lang_dir=None):
    global _parser
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    path = os.path.join(lang_dir or os.path.join(get_app_dir(), "lang"),
                        LANG_FILES.get(code, LANG_FILES[DEFAULT_LANG]))
    parser.read(path, encoding="utf-8")
    _parser = parser


def set_scope(name):
    global _scope
    _scope = name


def T(key, **kw):
    for section in (_scope, "common"):
        if _parser.has_option(section, key):
            value = _parser.get(section, key).replace("\\n", "\n")
            return value.format(**kw) if kw else value
    return f"[{key}]"
```

- [ ] **Step 5: Lancer les tests, ils passent**

Run: `python -m pytest tests/test_config.py tests/test_i18n.py -v`
Expected: 6 PASS

- [ ] **Step 6: Commit**

```bash
git add core/config.py core/i18n.py tests/conftest.py tests/test_config.py tests/test_i18n.py
git commit -m "feat: configuration partagee et traductions par portee de structure"
```

---

### Task 4: Orchestration de la generation

**Files:**
- Create: `core/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `core.ad_api.check_port/new_project/open_project/close_project`, `core.i18n.T`.
- Produces: `core.runner.run_generation(structure, p, host, log) -> bool`. `structure` expose `build(host, p, log) -> list[tuple[str, object]]`. `p` contient au moins `fto: str` et `nouveau_projet: bool`. `log` est un callable `log(msg: str)`. Retourne `True` si tout a reussi ; toute exception est journalisee et le projet est ferme.

- [ ] **Step 1: Ecrire les tests**

`tests/test_runner.py` :

```python
from types import SimpleNamespace

from core import ad_api
from core.runner import run_generation


def _patch(monkeypatch):
    calls = []
    monkeypatch.setattr(ad_api, "check_port", lambda host: calls.append("port"))
    monkeypatch.setattr(ad_api, "new_project", lambda host, fto: calls.append("new"))
    monkeypatch.setattr(ad_api, "open_project", lambda host, fto: calls.append("open"))
    monkeypatch.setattr(ad_api, "close_project", lambda host: calls.append("close"))
    return calls


def test_success_new_project(monkeypatch):
    calls = _patch(monkeypatch)
    lines = []
    s = SimpleNamespace(build=lambda host, p, log: [("Portiques", 5)])
    ok = run_generation(s, {"fto": "C:\\a.fto", "nouveau_projet": True}, "http://h", lines.append)
    assert ok is True
    assert calls == ["port", "new", "close"]
    assert any("Portiques" in l and "5" in l for l in lines)


def test_open_existing(monkeypatch):
    calls = _patch(monkeypatch)
    s = SimpleNamespace(build=lambda host, p, log: [])
    run_generation(s, {"fto": "C:\\a.fto", "nouveau_projet": False}, "http://h", lambda m: None)
    assert calls == ["port", "open", "close"]


def test_error_is_logged_and_project_closed(monkeypatch):
    calls = _patch(monkeypatch)
    lines = []

    def boom(host, p, log):
        raise RuntimeError("API KO")

    ok = run_generation(SimpleNamespace(build=boom), {"fto": "x", "nouveau_projet": True},
                        "http://h", lines.append)
    assert ok is False
    assert calls[-1] == "close"
    assert any("log_erreur" in l for l in lines)
```

- [ ] **Step 2: Lancer les tests, ils echouent**

Run: `python -m pytest tests/test_runner.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'core.runner'`

- [ ] **Step 3: Ecrire `core/runner.py`**

```python
from core import ad_api
from core.i18n import T

SEP = "=" * 52


def run_generation(structure, p, host, log):
    try:
        log(SEP)
        log(T("log_fichier", path=p["fto"]))
        log(T("log_api", host=host))
        log(SEP)

        log(T("log_verif_port"))
        ad_api.check_port(host)
        log(T("log_api_ok"))

        if p["nouveau_projet"]:
            log(T("log_nouveau_projet", path=p["fto"]))
            ad_api.new_project(host, p["fto"])
            log(T("log_nouveau_projet_ok"))
        else:
            log(T("log_ouverture", path=p["fto"]))
            ad_api.open_project(host, p["fto"])
            log(T("log_ouverture_ok"))

        rows = structure.build(host, p, log)

        log(T("log_fermeture"))
        ad_api.close_project(host)
        log(T("log_fermeture_ok"))

        log(SEP)
        log(T("syn_succes"))
        log(SEP)
        for label, value in rows:
            log(f"  {label:<26}: {value}")
        log(SEP)
        return True
    except Exception as ex:
        log(T("log_erreur", ex=ex))
        ad_api.close_project(host)
        return False
```

`close_project` ignore deja ses propres exceptions (voir `core/ad_api.py`).

- [ ] **Step 4: Lancer les tests, ils passent**

Run: `python -m pytest tests/test_runner.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add core/runner.py tests/test_runner.py
git commit -m "feat: orchestration de generation commune aux structures"
```

---

### Task 5: Structure Antenne

**Files:**
- Create: `structures/__init__.py` (vide pour l'instant), `structures/antenna.py`
- Test: `tests/test_antenna.py`

**Interfaces:**
- Consumes: `core.ad_api.*`, `core.i18n.T`.
- Produces (contrat) : `KEY = "antenna"`, `TITLE_KEY = "structure_antenna"`, `ICON`, `DEFAULT_MATERIAL = "S235"`, `ELEMENTS`, `DEFAULTS`, `render_form()`, `preview(p) -> plotly Figure` (sans hauteur), `validate(p)` (leve `ValueError`), `build(host, p, log) -> list[tuple[str, object]]`. Aussi : `generate_antenna_tower(...)`, `parse_heights(text) -> list[float]`.
- Cles de `p` : `height, base_type, num_levels, base_size, guy_levels, guy_heights (str "20,40"), anchor_distance, creer_systemes, section, section_guy, M`.
- Cles de session : `"antenna.<nom>"` pour chaque cle de `DEFAULTS`.

- [ ] **Step 1: Ecrire les tests**

`tests/test_antenna.py` :

```python
import pytest

from core import ad_api
from structures import antenna
from structures.antenna import generate_antenna_tower


def _p(**kw):
    p = {"height": 40.0, "base_type": "square", "num_levels": 40, "base_size": 0.6,
         "guy_levels": 2, "guy_heights": "20,40", "anchor_distance": 20.0,
         "creer_systemes": False, "section": "CHS88.9x3C", "section_guy": "CHS21.3x2C", "M": "S235"}
    p.update(kw)
    return p


def test_triangle_no_guys():
    m = generate_antenna_tower(20, "triangle", 20, 0.5)["metadata"]
    assert m["total_nodes"] == 63
    assert m["total_elements"] == 180
    assert m["total_supports"] == 3
    assert m["total_guy_wires"] == 0
    assert m["total_anchors"] == 0


def test_square_with_guys():
    p = generate_antenna_tower(40, "square", 40, 0.6, guy_levels=2, guy_heights=[20, 40], anchor_distance=20)
    m = p["metadata"]
    assert m["total_elements"] == 480
    assert m["total_supports"] == 4
    assert m["total_guy_wires"] == 8
    assert m["total_anchors"] == 4


def test_build_counts(monkeypatch):
    calls = {"lin": 0, "sup": 0, "sec": 0}
    monkeypatch.setattr(ad_api, "create_material", lambda *a, **k: 1)
    monkeypatch.setattr(ad_api, "create_system", lambda *a, **k: 9)

    def count(name):
        def f(*a, **k):
            calls[name] += 1
            return 2
        return f

    monkeypatch.setattr(ad_api, "create_section", count("sec"))
    monkeypatch.setattr(ad_api, "create_linear_element", count("lin"))
    monkeypatch.setattr(ad_api, "create_support", count("sup"))

    rows = antenna.build("http://h", _p(), lambda m: None)

    assert calls == {"lin": 480 + 8, "sup": 4 + 4, "sec": 2}
    assert rows[-1][1] == 480 + 8 + 4 + 4


@pytest.mark.parametrize("text", ["abc", "20;40", "20,,x"])
def test_bad_guy_heights_is_validation_error(text):
    with pytest.raises(ValueError, match="ui_guy_heights_invalid"):
        antenna.validate(_p(guy_heights=text))


def test_guy_heights_order_and_count():
    with pytest.raises(ValueError, match="val_guy_order"):
        antenna.validate(_p(guy_heights="40,20"))
    with pytest.raises(ValueError, match="val_guy_count"):
        antenna.validate(_p(guy_heights="20"))


def test_preview_bad_heights_raises():
    with pytest.raises(ValueError):
        antenna.preview(_p(guy_heights="abc"))


def test_preview_ok():
    fig = antenna.preview(_p())
    assert len(fig.data) == 3
```

Note : sans fichier de langue charge, `T("cle")` renvoie `"[cle]"`, d'ou les `match=` sur les noms de cles.

- [ ] **Step 2: Lancer les tests, ils echouent**

Run: `python -m pytest tests/test_antenna.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'structures'`

- [ ] **Step 3: Creer le module**

```bash
mkdir -p structures
: > structures/__init__.py
```

`structures/antenna.py` : commencer par l'en-tete ci-dessous, puis copier **sans modification** `validate_inputs` et `generate_antenna_tower` depuis `Originals/Antenna Generator/antenna_tower.py` (lignes 11-249), puis ajouter le reste.

```python
"""Pylone antenne treillis (base triangle ou carre) avec haubans optionnels."""
import math

import streamlit as st

from core import ad_api
from core.i18n import T

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


# --- validate_inputs et generate_antenna_tower copies ici depuis antenna_tower.py ---


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
    st.markdown(f":material/square_foot: **{T('ui_web_geo')}**")
    g1, g2, g3, g4 = st.columns(4)
    g1.number_input(T("ui_height"), min_value=0.1, max_value=999.0, step=0.5, format="%.2f",
                    key=_k("height"), on_change=_refill_guy_heights)
    g2.number_input(T("ui_num_levels"), min_value=1, max_value=200, step=1, key=_k("num_levels"))
    g3.number_input(T("ui_base_size"), min_value=0.01, max_value=99.0, step=0.05, format="%.2f",
                    key=_k("base_size"))
    g4.segmented_control(T("ui_base_type"), options=BASE_TYPES, format_func=lambda v: T(f"base_{v}"),
                         key=_k("base_type"), required=True)

    st.markdown(f":material/cable: **{T('ui_web_haubans')}**")
    h1, h2, h3, h4 = st.columns(4, vertical_alignment="bottom")
    h1.number_input(T("ui_guy_levels"), min_value=0, max_value=20, step=1,
                    key=_k("guy_levels"), on_change=_refill_guy_heights)
    h2.text_input(T("ui_guy_heights"), key=_k("guy_heights"), placeholder="20,40")
    h3.number_input(T("ui_anchor_distance"), min_value=0.0, max_value=999.0, step=0.5, format="%.2f",
                    key=_k("anchor_distance"))
    h4.checkbox(T("ui_creer_systemes"), key=_k("creer_systemes"))


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

    gl = int(p["guy_levels"])
    if gl > 0:
        try:
            gh = parse_heights(p["guy_heights"])
        except ValueError:
            raise ValueError(T("ui_guy_heights_invalid"))
        if len(gh) != gl:
            errors.append(T("val_guy_count", n=gl))
        else:
            if any(h <= 0 or h > float(p["height"]) for h in gh):
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
    rows.append((T("syn_section", nom=p["section"]), ""))
    if counts["guy_wires"]:
        rows.append((T("syn_section_guy", nom=p["section_guy"]), ""))
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
```

- [ ] **Step 4: Lancer les tests, ils passent**

Run: `python -m pytest tests/test_antenna.py -v`
Expected: 9 PASS

- [ ] **Step 5: Commit**

```bash
git add structures/__init__.py structures/antenna.py tests/test_antenna.py
git commit -m "feat: structure antenne au format module"
```

---

### Task 6: Structure Portique

**Files:**
- Create: `structures/steel_frame.py`
- Test: `tests/test_steel_frame.py`

**Interfaces:**
- Consumes: `core.ad_api.*`, `core.i18n.T`.
- Produces (contrat) : `KEY = "steel_frame"`, `TITLE_KEY = "structure_steel_frame"`, `ICON`, `DEFAULT_MATERIAL = "S275"`, `ELEMENTS`, `DEFAULTS`, `render_form()`, `preview(p)`, `validate(p)`, `build(host, p, log) -> list[tuple[str, object]]`.
- Cles de `p` : `n, e, Hg, Hd, L, AR, F, TypeAppui, Npg, Npd, Dbg, Dbd, creer_parois, creer_systemes, Sp, Sa, Sn, M`.

- [ ] **Step 1: Ecrire les tests**

`tests/test_steel_frame.py` :

```python
import pytest

from core import ad_api
from structures import steel_frame


def _p(**kw):
    p = {"n": 5, "e": 5.0, "Hg": 6.0, "Hd": 4.0, "L": 18.0, "AR": 7.0, "F": 1.2,
         "TypeAppui": "HINGED", "Npg": 5, "Npd": 7, "Dbg": 0.3, "Dbd": 0.3,
         "creer_parois": True, "creer_systemes": False,
         "Sp": "HEA400", "Sa": "IPE400", "Sn": "IPE160", "M": "S275"}
    p.update(kw)
    return p


def test_build_counts(monkeypatch):
    calls = {"lin": 0, "sup": 0, "sec": 0, "area": 0}
    monkeypatch.setattr(ad_api, "create_material", lambda *a, **k: 1)
    monkeypatch.setattr(ad_api, "create_system", lambda *a, **k: 9)
    monkeypatch.setattr(ad_api, "create_dead_load_case", lambda *a, **k: (3, 4))

    def count(name):
        def f(*a, **k):
            calls[name] += 1
            return 2
        return f

    monkeypatch.setattr(ad_api, "create_section", count("sec"))
    monkeypatch.setattr(ad_api, "create_linear_element", count("lin"))
    monkeypatch.setattr(ad_api, "create_support", count("sup"))
    monkeypatch.setattr(ad_api, "create_load_area", count("area"))

    rows = steel_frame.build("http://h", _p(), lambda m: None)

    # 5 portiques x 4 barres + 4 travees x (5 + 7) pannes
    assert calls == {"lin": 20 + 48, "sup": 10, "sec": 3, "area": 6}
    assert rows[-1][1] == 20 + 48 + 10 + 6


def test_validate_ok():
    steel_frame.validate(_p())


def test_validate_ar_outside_span():
    with pytest.raises(ValueError, match="val_AR"):
        steel_frame.validate(_p(AR=18.0))


def test_validate_purlin_offset_too_long():
    with pytest.raises(ValueError, match="val_Dbg_long"):
        steel_frame.validate(_p(Dbg=50.0))


def test_preview_segments():
    fig = steel_frame.preview(_p())
    assert len(fig.data) == 3
```

- [ ] **Step 2: Lancer les tests, ils echouent**

Run: `python -m pytest tests/test_steel_frame.py -v`
Expected: FAIL, `ImportError: cannot import name 'steel_frame'`

- [ ] **Step 3: Ecrire `structures/steel_frame.py`**

```python
"""Portique metallique a deux versants avec pannes, parois et poids propre."""
import math

import streamlit as st

from core import ad_api
from core.i18n import T

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
    st.markdown(f":material/square_foot: **{T('ui_web_geo')}**")
    g1, g2, g3, g4 = st.columns(4)
    g1.number_input(T("ui_nb_portiques"), min_value=2, max_value=25, step=1, key=_k("n"))
    g1.number_input(T("ui_portee"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("L"))
    g2.number_input(T("ui_entraxe"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("e"))
    g2.number_input(T("ui_ar"), min_value=0.01, max_value=999.0, step=0.1, format="%.2f", key=_k("AR"))
    g3.number_input(T("ui_hg"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("Hg"))
    g3.number_input(T("ui_fleche"), min_value=0.01, max_value=999.0, step=0.01, format="%.2f", key=_k("F"))
    g4.number_input(T("ui_hd"), min_value=0.1, max_value=999.0, step=0.1, format="%.2f", key=_k("Hd"))
    g4.segmented_control(T("ui_type_appui"), options=APPUIS, format_func=lambda v: T(f"appui_{v.lower()}"),
                         key=_k("TypeAppui"), required=True)

    c1, c2 = st.columns(2)
    c1.checkbox(T("ui_creer_parois"), key=_k("creer_parois"))
    c2.checkbox(T("ui_creer_systemes"), key=_k("creer_systemes"))

    st.markdown(f":material/straighten: **{T('ui_web_pannes')}**")
    p1, p2, p3, p4 = st.columns(4)
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
```

Puis `build(host, p, log)` : copier le corps de `build_structure` de `Originals/SteelFrameGenerator/steel_frame_web.py` (lignes 622-774) avec ces transformations mecaniques, et rien d'autre :
1. `def build_structure(host, p, log_cb):` devient `def build(host, p, log):`, et chaque `log_cb(...)` devient `log(...)`.
2. Chaque appel `create_*(` devient `ad_api.create_*(`.
3. Chaque `T("cle", ...) or "texte"` devient `T("cle", ...)` (supprimer le repli `or ...`) ; supprimer aussi le second argument de tag (`, "ok"`) des appels de log.
4. `creer_parois = p.get("creer_parois", False)` devient `creer_parois = p["creer_parois"]` ; idem `creer_systemes = p["creer_systemes"]`.
5. Remplacer la ligne finale `total = sum(counts.values())` / `return counts, total, Lg, Ld, H_faitage` par :

```python
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
```

- [ ] **Step 4: Lancer les tests, ils passent**

Run: `python -m pytest tests/test_steel_frame.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add structures/steel_frame.py tests/test_steel_frame.py
git commit -m "feat: structure portique au format module"
```

---

### Task 7: Registre des structures et verification du contrat

**Files:**
- Modify: `structures/__init__.py`
- Test: `tests/test_registry.py`

**Interfaces:**
- Consumes: `structures.antenna`, `structures.steel_frame`, `core.profiles.PROFILES`, `core.ad_api.MATERIALS`.
- Produces: `structures.STRUCTURES: dict[str, module]`, ordre `steel_frame` puis `antenna` (le premier est la structure de repli).

- [ ] **Step 1: Ecrire le test**

`tests/test_registry.py` :

```python
import pytest

from core.ad_api import MATERIALS
from core.profiles import PROFILES
from structures import STRUCTURES

CONTRACT = ["KEY", "TITLE_KEY", "ICON", "DEFAULT_MATERIAL", "ELEMENTS", "DEFAULTS",
            "render_form", "preview", "validate", "build"]


def test_order():
    assert list(STRUCTURES) == ["steel_frame", "antenna"]


@pytest.mark.parametrize("key", list(STRUCTURES))
def test_contract(key):
    s = STRUCTURES[key]
    for attr in CONTRACT:
        assert hasattr(s, attr), f"{key}.{attr} manquant"
    assert s.KEY == key
    assert s.DEFAULT_MATERIAL in MATERIALS
    assert not set(s.ELEMENTS) & set(s.DEFAULTS)
    assert "M" not in s.DEFAULTS
    for name, (label_key, families, default) in s.ELEMENTS.items():
        assert all(f in PROFILES for f in families), f"{key}.{name} : famille inconnue"
        assert any(default in PROFILES[f] for f in families), f"{key}.{name} : {default} hors familles"
```

- [ ] **Step 2: Lancer le test, il echoue**

Run: `python -m pytest tests/test_registry.py -v`
Expected: FAIL, `ImportError: cannot import name 'STRUCTURES'`

- [ ] **Step 3: Ecrire `structures/__init__.py`**

```python
from structures import antenna, steel_frame

# Ajouter une structure : creer structures/<nom>.py (voir le contrat dans la spec) et l'inscrire ici.
STRUCTURES = {
    "steel_frame": steel_frame,
    "antenna": antenna,
}
```

- [ ] **Step 4: Lancer toute la suite**

Run: `python -m pytest -v`
Expected: tout PASS

- [ ] **Step 5: Commit**

```bash
git add structures/__init__.py tests/test_registry.py
git commit -m "feat: registre des structures et test du contrat"
```

---

### Task 8: Fichiers de langue fusionnes

**Files:**
- Create: `lang/fr.ini`, `lang/en.ini`, `lang/pl.ini`
- Test: `tests/test_lang_files.py`

**Interfaces:**
- Consumes: `Originals/*/{french,english,polish}.ini` (section `[messages]`).
- Produces: fichiers `[common]`, `[steel_frame]`, `[antenna]` lus par `core.i18n`.

La suppression des cles inutilisees se fait en Task 10, une fois `core/ui.py` et `app.py` ecrits. Ici on fusionne tout.

- [ ] **Step 1: Ecrire le test**

`tests/test_lang_files.py` :

```python
import configparser
import os
import re

import pytest

from core.i18n import LANG_FILES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Le code commun (app.py, core/) doit trouver ses cles dans [common] quelle que soit la structure active.
SOURCES = {
    "common": ["app.py", "core/ui.py", "core/runner.py"],
    "steel_frame": ["structures/steel_frame.py"],
    "antenna": ["structures/antenna.py"],
}
# Cles non appelees par T("...") litteral : TITLE_KEY, libelles de ELEMENTS, format_func dynamiques.
EXTRA = {
    "common": {"structure_steel_frame", "structure_antenna"},
    "steel_frame": {"ui_sec_poteaux", "ui_sec_arbaletriers", "ui_sec_pannes", "appui_hinged", "appui_fixed"},
    "antenna": {"ui_section", "ui_section_guy", "base_triangle", "base_square"},
}


def _keys(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return set(re.findall(r'T\(\s*["\']([A-Za-z_]+)["\']', f.read()))


@pytest.mark.parametrize("code", list(LANG_FILES))
def test_used_keys_translated_in_scope(code):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(os.path.join(ROOT, "lang", LANG_FILES[code]), encoding="utf-8")
    for scope, files in SOURCES.items():
        keys = EXTRA[scope].union(*(_keys(rel) for rel in files))
        for key in keys:
            assert parser.has_option(scope, key) or parser.has_option("common", key), \
                f"{code}: [{scope}] {key} absente"
```

- [ ] **Step 2: Lancer le test, il echoue**

Run: `python -m pytest tests/test_lang_files.py -v`
Expected: FAIL, `cle ... absente` (le dossier `lang/` n'existe pas)

- [ ] **Step 3: Generer les fichiers avec ce script ponctuel (non versionne)**

Enregistrer dans le scratchpad sous `merge_lang.py` puis lancer `python <scratchpad>/merge_lang.py` depuis la racine :

```python
import configparser
import os

SRC = {"fr": "french.ini", "en": "english.ini", "pl": "polish.ini"}
NEW = {
    "fr": {"ui_structure": "Structure", "structure_steel_frame": "Portique métallique",
           "structure_antenna": "Pylône antenne",
           "ui_apercu_indisponible": "Aperçu indisponible : géométrie invalide."},
    "en": {"ui_structure": "Structure", "structure_steel_frame": "Steel frame",
           "structure_antenna": "Antenna tower",
           "ui_apercu_indisponible": "Preview unavailable: invalid geometry."},
    "pl": {"ui_structure": "Konstrukcja", "structure_steel_frame": "Rama stalowa",
           "structure_antenna": "Wieża antenowa",
           "ui_apercu_indisponible": "Podgląd niedostępny: nieprawidłowa geometria."},
}


# Cles propres au Portique mais utilisees par le code commun (core/ui.py).
PROMOTE = ["ui_btn_ouvrir_journal"]


def read(path):
    p = configparser.ConfigParser(interpolation=None)
    p.optionxform = str
    p.read(path, encoding="utf-8")
    return dict(p["messages"])


os.makedirs("lang", exist_ok=True)
for code, name in SRC.items():
    sf = read(os.path.join("Originals", "SteelFrameGenerator", name))
    at = read(os.path.join("Originals", "Antenna Generator", name))
    out = configparser.ConfigParser(interpolation=None)
    out.optionxform = str
    out["common"] = {**{k: v for k, v in sf.items() if k in at or k in PROMOTE}, **NEW[code]}
    out["steel_frame"] = {k: v for k, v in sf.items() if k not in at and k not in PROMOTE}
    out["antenna"] = {k: v for k, v in at.items() if k not in sf}
    with open(os.path.join("lang", f"{code}.ini"), "w", encoding="utf-8") as f:
        out.write(f)
    print(code, len(out["common"]), len(out["steel_frame"]), len(out["antenna"]))
```

Expected : `fr 52 132 41`, puis la meme chose pour `en` et `pl`.

- [ ] **Step 4: Lancer le test, il passe**

Run: `python -m pytest tests/test_lang_files.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add lang/ tests/test_lang_files.py
git commit -m "feat: fichiers de langue fusionnes common / steel_frame / antenna"
```

---

### Task 9: Interface commune et application

**Files:**
- Create: `core/ui.py`, `app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: tout ce qui precede.
- Produces: `core.ui` avec `PREVIEW_HEIGHT`, `DEFAULT_HOST`, `inject_css()`, `init_session()`, `keep_widget_state()`, `settings_panel()`, `project_panel()`, `sections_panel(key, elements)`, `collect_params(key, structure) -> dict`, `project_path() -> str | None`, `preview_panel(key, p)`, `actions_row() -> bool`, `journal_button()`. `app.py` avec `VERSION = "2.0"` et `main()`.
- Convention de session : toute cle contenant un point (`"steel_frame.n"`, `"project.fto"`, `"settings.host"`) est reinjectee a chaque execution par `keep_widget_state()` pour survivre au nettoyage des widgets non affiches. Les cles sans point (`"structure"`, `"log_lines"`, `"last_result"`, `"api_proc"`, cles de boutons) ne le sont pas.

**Avant le Step 3, invoquer le skill `frontend-design`** : la mise en page ci-dessous est fixee par la spec (colonnes 2/3 - 1/3, liste deroulante dans l'en-tete, blocs dans cet ordre, hauteur totale ~700 px) ; le skill sert a affiner le CSS dans `inject_css()` (hierarchie des titres de blocs, grille, lisibilite de l'etat API) sans ajouter de hauteur ni de dependance, et en gardant le theme de `.streamlit/config.toml`.

- [ ] **Step 1: Ecrire les tests**

`tests/test_app.py` :

```python
import os

import pytest
from streamlit.testing.v1 import AppTest

from core import config
from core.profiles import PROFILES

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


@pytest.fixture
def cfg_file(tmp_path, monkeypatch):
    path = tmp_path / "config.ini"
    monkeypatch.setattr(config, "CONFIG_FILE", str(path))
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
```

- [ ] **Step 2: Lancer les tests, ils echouent**

Run: `python -m pytest tests/test_app.py -v`
Expected: FAIL (`app.py` introuvable)

- [ ] **Step 3: Ecrire `core/ui.py`**

```python
"""Blocs d'interface communs a toutes les structures."""
import os
import subprocess

import streamlit as st

from core import ad_api
from core.config import load_config, save_config
from core.i18n import LANG_LABELS, T
from core.profiles import PROFILES
from structures import STRUCTURES

PREVIEW_HEIGHT = 600
DEFAULT_HOST = "http://localhost:52000"

_CSS = """
<style>
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }

    .block-container { padding-top: 1.7rem !important; padding-bottom: 0.5rem !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.35rem !important; }

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
        st.caption("[GitHub API](https://github.com/Graitec-Group/advance-design-api) · "
                   "[Graitec](https://www.graitec.com)")


def _api_block():
    ss = st.session_state
    proc = ss.api_proc
    if proc is not None and proc.poll() is None:
        st.caption(f":green[:material/check_circle: {T('ui_api_active')}]")
        if st.button(T("ui_btn_stop_api"), icon=":material/stop:", width="stretch"):
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            ss.api_proc = None
            st.rerun()
    else:
        st.caption(T("ui_api_inactive"))
        if st.button(T("ui_btn_start_api"), icon=":material/play_arrow:", width="stretch"):
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
    st.markdown(f":material/folder: **{T('ui_web_projet')}**")
    pj1, pj2, pj3 = st.columns([1, 2, 1], vertical_alignment="bottom")
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
    st.markdown(f":material/hardware: **{T('ui_web_sections')}**")
    items = list(elements.items()) + [("M", None)]
    for i in range(0, len(items), 2):
        cols = st.columns([1, 2, 1, 2])
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
    clicked = c1.button(T("ui_btn_creer"), icon=":material/play_arrow:", type="primary", width="stretch")
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


def _journal_body():
    st.code("\n".join(st.session_state.log_lines), language=None, height=500)


def journal_button():
    if st.button(T("ui_btn_ouvrir_journal"), icon=":material/receipt_long:", width="stretch",
                 disabled=not st.session_state.log_lines):
        st.dialog(T("ui_journal_execution"), width="large")(_journal_body)()
```

- [ ] **Step 4: Ecrire `app.py`**

```python
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

VERSION = "2.0"

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

    h1, h2 = st.columns([3, 1], vertical_alignment="bottom")
    h1.subheader(f"{structure.ICON} Structure Generator  v{VERSION}")
    h2.selectbox(T("ui_structure"), list(STRUCTURES), format_func=lambda k: T(STRUCTURES[k].TITLE_KEY),
                 key="structure", on_change=lambda: save_config(structure=st.session_state.structure))

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
```

- [ ] **Step 5: Lancer les tests d'interface**

Run: `python -m pytest tests/test_app.py -v`
Expected: 5 PASS. Si `test_values_survive_structure_switch` echoue, verifier que `keep_widget_state()` est appele avant tout widget et que les cles concernees contiennent un point.

- [ ] **Step 6: Verification visuelle**

Run: `python -m streamlit run app.py --server.port 8501`
Verifier dans Chrome a 1920x1080 (barre de favoris affichee, fenetre maximisee) :
- les deux structures s'affichent sans barre de defilement verticale ;
- changer la langue en EN met a jour tous les libelles, sans aucun `[cle]` visible ;
- changer de famille de profil met a jour la liste des profils ;
- avec des hauteurs de haubans `abc`, l'apercu affiche le message d'indisponibilite.
Tout `[cle]` visible : ajouter la cle manquante dans `lang/*.ini` (section `[common]` si utilisee par `core/` ou `app.py`).

- [ ] **Step 7: Commit**

```bash
git add core/ui.py app.py tests/test_app.py
git commit -m "feat: application unifiee avec selection de structure"
```

---

### Task 10: Nettoyage des langues, lanceur et CHANGELOG

**Files:**
- Modify: `lang/fr.ini`, `lang/en.ini`, `lang/pl.ini`
- Create: `start.bat`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `tests/test_lang_files.py` (Task 8) comme garde-fou apres suppression.

- [ ] **Step 1: Supprimer les cles non referencees (script ponctuel, scratchpad)**

```python
import configparser
import os
import re

CODE = ["app.py", "core/ui.py", "core/runner.py", "structures/antenna.py", "structures/steel_frame.py"]
text = "".join(open(p, encoding="utf-8").read() for p in CODE)
literals = set(re.findall(r'["\']([A-Za-z_]+)["\']', text))
DYNAMIC = ("base_", "appui_")

for code in ("fr", "en", "pl"):
    path = os.path.join("lang", f"{code}.ini")
    p = configparser.ConfigParser(interpolation=None)
    p.optionxform = str
    p.read(path, encoding="utf-8")
    removed = 0
    for section in p.sections():
        for key in list(p[section]):
            if key not in literals and not key.startswith(DYNAMIC):
                del p[section][key]
                removed += 1
    with open(path, "w", encoding="utf-8") as f:
        p.write(f)
    print(code, "supprimees :", removed)
```

- [ ] **Step 2: Verifier que rien d'utilise n'a disparu**

Run: `python -m pytest -v`
Expected: tout PASS (dont `test_lang_files.py` et `test_app.py`)

- [ ] **Step 3: Ecrire `start.bat`**

Copier `Originals/SteelFrameGenerator/start.bat` vers `start.bat`, puis :
- remplacer chaque `Steel Frame Generator` par `Structure Generator` ;
- `set "SCRIPT=%APP_DIR%steel_frame_web.py"` devient `set "SCRIPT=%APP_DIR%app.py"` ;
- `python -m pip install --quiet --upgrade streamlit requests` devient `python -m pip install --quiet --upgrade streamlit requests plotly` ;
- `echo  Make sure start.bat and steel_frame_web.py` devient `echo  Make sure start.bat and app.py`.

Run: `grep -n "steel_frame_web\|Steel Frame" start.bat`
Expected: aucune ligne

- [ ] **Step 4: Ecrire `CHANGELOG.md`**

```markdown
# Changelog

## 2.0 - 2026-09-24
- Fusion de SteelFrameGenerator (1.32) et Antenna Generator (1.0) en une seule application, choix de la structure par liste deroulante
- Architecture modulaire : une structure = un module dans `structures/` + une ligne dans le registre
- Profils choisis par famille puis par nom, familles autorisees par element (catalogue Advance Design complet, 35 familles)
- Antenne : profils tubulaires circulaires, rectangulaires, carres et cornieres (CHSC, CHSH, RHSC, RHSH, SHSC, SHSH, L, Li)
- Materiaux S450 et S460 ajoutes
- Fichiers de langue FR/EN/PL fusionnes ; configuration unique `config.ini` (memorise la derniere structure)
- Interface compacte pour ecran 1920x1080 ; schema PNG de secours remplace par un message quand la geometrie est invalide
```

- [ ] **Step 5: Lancement reel**

Run: `start.bat -nodep`
Expected: le navigateur s'ouvre sur `http://localhost:8501`, l'application s'affiche. Si Advance Design 2027 est installe : "Demarrer l'API", generer un portique puis une antenne dans deux nouveaux projets, et verifier que le journal se termine par la synthese.

- [ ] **Step 6: Commit**

```bash
git add lang/ start.bat CHANGELOG.md
git commit -m "chore: nettoyage des traductions, lanceur unique, CHANGELOG 2.0"
```

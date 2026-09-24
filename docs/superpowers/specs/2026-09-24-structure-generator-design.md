# Structure Generator - Design

Date : 2026-09-24
Version cible : 2.0

## Objectif

Regrouper `Originals/SteelFrameGenerator` et `Originals/Antenna Generator` dans une seule application Streamlit, et permettre d'ajouter d'autres structures parametriques en ecrivant un module Python et en ajoutant une ligne au registre.

Criteres de reussite :
- Une liste deroulante choisit la structure (Portique, Antenne).
- L'interface reprend le modele `steel_frame_web.py` et tient sur un ecran 1920x1080 sans defilement (hauteur utile visee : ~900 px).
- Les profils sont choisis par famille puis par nom, depuis le module `core/profiles.py`, parmi les familles autorisees pour chaque element.
- Materiaux : S235, S275, S355, S450, S460.
- Le comportement de generation des deux structures est identique a celui des originaux.

Hors perimetre : beton, bois, sauvegarde des valeurs de geometrie, donnees de profils autres que le nom.

## Architecture

```
Structure Generator/
  app.py                    # point d'entree Streamlit + lanceur PyInstaller
  start.bat                 # installe streamlit, requests, plotly puis lance app.py
  CHANGELOG.md              # historique : version, date, sommaire des changements importants
  config.ini                # [General] language, api_server_exe, structure (ignore par git)
  .streamlit/config.toml    # theme (existant)
  AD_Profiles.md            # export Advance Design local, non versionne (.gitignore), non distribue
  API Data/                 # swagger.json + API_Commands.md : reference pour ajouter des appels a core/ad_api.py (.gitignore)
  core/
    ad_api.py               # copie de advance_design_api.py, STEEL_PROPS + S450, S460
    profiles.py             # PROFILES = {famille: [noms]} genere, seule source des profils a l'execution
    i18n.py                 # LANG_LABELS, load_language(code), set_scope(structure), T(key, **kw)
    config.py               # get_app_dir, load_config, save_config
    ui.py                   # CSS compact + blocs communs
    runner.py               # run_generation(structure, params, host)
  structures/
    __init__.py             # STRUCTURES = {"steel_frame": steel_frame, "antenna": antenna}
    steel_frame.py
    antenna.py              # inclut generate_antenna_tower (ex antenna_tower.py)
  lang/fr.ini, en.ini, pl.ini
  tools/
    gen_profiles.py         # regenere core/profiles.py depuis AD_Profiles.md (usage developpeur)
  tests/
```

`Originals/` reste en place comme reference en lecture seule ; aucun module ne l'importe.

## Contrat d'une structure

Chaque module de `structures/` expose :

| Attribut | Description |
|---|---|
| `KEY` | Cle du registre (ex. `"antenna"`), prefixe des cles de session |
| `TITLE_KEY` | Cle i18n `[common]` du libelle dans la liste deroulante |
| `DEFAULT_MATERIAL` | Materiau par defaut (ex. `"S275"`) |
| `ICON` | Icone Material Streamlit (ex. `:material/foundation:`) |
| `ELEMENTS` | `{param: (label_key, [familles autorisees], profil_defaut)}` ; ordre = ordre d'affichage |
| `DEFAULTS` | `{param: valeur}` pour la geometrie et les options propres |
| `render_form()` | Dessine les blocs propres a la structure (geometrie, pannes, haubans...) |
| `preview(p)` | Retourne une figure Plotly 3D filaire |
| `validate(p)` | Leve `ValueError` (messages traduits, joints par `\n`) |
| `build(host, p, log)` | Cree les objets via `core.ad_api` ; retourne `[(label, valeur), ...]` pour la synthese |

`p` contient les parametres de la structure, les profils choisis (cles de `ELEMENTS`), `M` (materiau), `fto` et `nouveau_projet`.

Ajouter une structure = creer `structures/<nom>.py` respectant ce contrat + une ligne dans `STRUCTURES` + une section `[<nom>]` dans chaque fichier de langue + la cle `TITLE_KEY` (ex. `structure_<nom>`) dans la section `[common]` de chaque fichier de langue (le selecteur affiche tous les titres quelle que soit la structure active). `tests/test_registry.py` et `tests/test_lang_files.py` verifient automatiquement toute structure inscrite.

### Portique (`steel_frame`)

Reprise de la logique de `steel_frame_web.py` (geometrie, pannes, parois, systemes, poids propre).

| Element | Familles autorisees | Defaut |
|---|---|---|
| `Sp` poteaux | HEA, HEB, HEM, IPE | HEA400 |
| `Sa` arbaletriers | HEA, HEB, HEM, IPE | IPE400 |
| `Sn` pannes | IPE, IPN, UPN, UPE, HEA | IPE160 |

Materiau par defaut : S275.

### Antenne (`antenna`)

Reprise de `antenna_tower.py` et `antenna_tower_web.py` (treillis triangle/carre, haubans, ancrages).

| Element | Familles autorisees | Defaut |
|---|---|---|
| `section` montants/treillis | CHSC, CHSH, RHSC, RHSH, SHSC, SHSH, L, Li | CHS88.9x3C |
| `section_guy` haubans | CHSC, CHSH, RHSC, RHSH, SHSC, SHSH, L, Li | CHS21.3x2C |

Materiau par defaut : S235.

## Flux de donnees

1. `app.py` lit `config.ini`, choisit la structure (derniere utilisee, sinon `steel_frame`), initialise la session.
2. Etat de session prefixe par structure (`steel_frame.n`, `antenna.height`, ...) et stocke hors cles de widget : Streamlit efface l'etat d'un widget non rendu, sinon les saisies seraient perdues en changeant de structure.
3. Changement de structure : enregistrement dans `config.ini`, `st.rerun()`.
4. Bouton Generer : `app.py` assemble `p`, appelle `structure.validate(p)`, puis `runner.run_generation(structure, p, host)` sous `st.spinner`.
5. `run_generation` : en-tete du journal -> `check_port` -> `new_project` ou `open_project` -> `structure.build` -> `close_project` -> synthese (lignes retournees par `build`). En cas d'exception : ligne d'erreur, `last_result = "error"`, tentative de `close_project`.

## Interface (1920x1080)

Colonnes 2/3 (formulaire) et 1/3 (apercu), CSS compact de `steel_frame_web.py` (champs de 34 px).

```
+--------------------------------------------------------------+---------------------------+
| [icone] Structure Generator  v2.0     [Structure: Portique v]|                           |
| > Parametres (langue, URL API, exe, liens)      (replie)     |                           |
| Projet   [x] Nouveau  [nom / chemin .fto      ][dossier] [API]|   Apercu 3D Plotly        |
|--------------------------------------------------------------|   (hauteur ~600 px)       |
| render_form() de la structure                                |                           |
|--------------------------------------------------------------|                           |
| Sections & Materiau (genere depuis ELEMENTS)                 |                           |
|  [Famille][Profil      ]  [Famille][Profil      ]           |                           |
|  [Famille][Profil      ]  [Materiau]                         |                           |
+--------------------------------------------------------------+---------------------------+
| [> Generer la structure] [corbeille]  statut                 |  [Ouvrir le journal]      |
+--------------------------------------------------------------+---------------------------+
```

- Liste deroulante de structure dans l'en-tete, sur la ligne du titre.
- Suppression de la legende sous le titre et du pied de page ; liens GitHub/Graitec dans le panneau Parametres.
- Bloc Sections : deux elements par ligne (Famille 1 / Profil 2 / Famille 1 / Profil 2), le materiau occupe la case suivante. Changer de famille selectionne le premier profil de la famille si le profil courant n'y figure pas.
- Journal dans une boite de dialogue (`st.dialog`), comme le modele.
- Hauteur d'apercu unique definie dans `core/ui.py`.
- Theme sombre de `config.toml` conserve ; soin porte a la hierarchie des titres de blocs, a l'alignement en grille et a la lisibilite de l'etat API (skill `frontend-design` a l'implementation).

## Configuration, langues, catalogue

- `config.ini` : `[General]` avec `language`, `api_server_exe`, `structure`. Valeurs par defaut : `fr`, `C:\Program Files\Graitec\Advance Design\2027\Bin\AD.API.Srv.exe`, `steel_frame`.
- Fichiers de langue : `[common]` pour les cles presentes dans les deux originaux (en cas de texte different, la valeur du Portique, modele de l'interface, est retenue), `[steel_frame]` et `[antenna]` pour les cles propres a chaque original. Les cles non referencees par le nouveau code sont supprimees. `T(key)` cherche dans la section de la structure active puis dans `[common]`. Cle absente : retourne `[key]`. Les replis `T(...) or "texte"` des originaux sont supprimes.
- `core/profiles.py` : module Python de donnees, `PROFILES = {famille: [noms]}` (35 familles, noms uniquement, aucune donnee mecanique). Il est versionne et distribue ; `AD_Profiles.md` ne l'est pas.
- `tools/gen_profiles.py` : lit `AD_Profiles.md`, detecte `## Famille <nom>`, prend la premiere cellule de chaque ligne de tableau hors en-tete (`| name |`) et separateur (`|---|`), puis ecrit `core/profiles.py`. Ordre des profils = ordre du fichier. A relancer uniquement quand le catalogue Advance Design change.

## Gestion des erreurs

- Validation : `ValueError` affichee par `st.error`, pas d'appel API.
- Generation : toute exception est journalisee, statut "echec", fermeture du projet tentee.
- API non demarree / exe introuvable : messages existants des originaux, conserves.

## Tests (pytest)

- `profiles` : `PROFILES` contient 35 familles ; `HEA400` dans `HEA` ; `CHS88.9x3C` dans `CHSC`.
- Registre : chaque structure expose tous les attributs du contrat ; chaque famille de `ELEMENTS` existe dans le catalogue ; chaque profil par defaut appartient a une de ses familles autorisees.
- Antenne : tests de geometrie repris de `tests/test_antenna_tower.py` ; comptage des appels API repris de `tests/test_build_structure.py` (monkeypatch de `core.ad_api`).
- Portique : comptage des appels API equivalent (poteaux, arbaletriers, pannes, appuis).
- `i18n` : repli section structure -> `[common]` -> `[key]`.

## Livraison

- `start.bat` unique, lance `app.py`, installe `streamlit requests plotly` (option `-nodep` conservee).
- Lanceur PyInstaller de `steel_frame_web.py` conserve dans `app.py`.
- Version 2.0.
- `CHANGELOG.md` : une entree par version, la plus recente en haut, format :
  ```
  ## 2.0 - 2026-09-24
  - Fusion de SteelFrameGenerator (1.32) et Antenna Generator (1.0) en une seule application
  - ...
  ```
  Mis a jour a chaque changement de version (`VERSION` dans `app.py`).

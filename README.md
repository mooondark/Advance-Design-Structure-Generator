# Advance Design Structure Generator

Français | [English](README_EN.md)

Générateur de structures métalliques paramétriques avec l'API d'Advance Design.
Regroupe et remplace [SteelFrameGenerator](https://github.com/mooondark/SteelFrameGenerator) et Antenna Generator.

## Structures disponibles

- **Portique métallique** : portiques 3D à deux versants, pannes, parois, poids propre
- **Pylône antenne** : treillis à base triangulaire ou carrée, nombre de niveaux paramétrable, haubans et ancrages optionnels

## Fonctionnalités

- Choix de la structure par liste déroulante
- Profilés choisis par famille puis par nom (catalogue Advance Design), familles adaptées à chaque élément
- Matériaux : S235, S275, S355, S450, S460
- Aperçu 3D interactif
- Démarrage et arrêt du serveur API depuis l'interface
- Langues incluses : FR/EN/PL
- Sauvegarde des options

## Lancement

Python 3 doit être installé et présent dans le PATH.

- Double-cliquer sur `start.bat` : installe ou met à jour les dépendances (streamlit, requests, plotly), puis ouvre l'application dans le navigateur
- `start.bat -nodep` : lance sans vérifier les dépendances
- Ou : `python -m streamlit run app.py`

## Ajouter une structure

1. Créer `structures/<nom>.py` en respectant le contrat : `KEY`, `TITLE_KEY`, `ICON`, `DEFAULT_MATERIAL`, `ELEMENTS`, `DEFAULTS`, `render_form()`, `preview(p)`, `validate(p)`, `build(host, p, log)` (exemples : `structures/steel_frame.py`, `structures/antenna.py`)
2. L'inscrire dans `STRUCTURES` (`structures/__init__.py`)
3. Ajouter ses traductions dans `lang/*.ini` : une section `[<nom>]`, et la clé `TITLE_KEY` dans `[common]`
4. Lancer les tests : `python -m pytest` (le contrat et les traductions de la nouvelle structure sont vérifiés automatiquement)

## Catalogue des profilés

`core/profiles.py` contient les noms des profilés par famille. Il est généré par `tools/gen_profiles.py` à partir d'un export `AD_Profiles.md` du catalogue Advance Design (non fourni).

## Documentation

- [Historique des versions](CHANGELOG.md)

**Attention, ce script nécessite l'utilisation de l'[API](https://github.com/Graitec-Group/advance-design-api) d'Advance Design**

**Une licence est également nécessaire afin de l'utiliser, et le logiciel AD2027 ou supérieur doit être installé**

Voir également [Advance Design Viewer](https://github.com/mooondark/ADViewer)

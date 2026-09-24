# Advance Design Structure Generator

Français | [English](README_EN.md)

Générateur de structures métalliques paramétriques avec l'API d'Advance Design.

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

## Documentation

- [Historique des versions](CHANGELOG.md)

**Attention, ce script nécessite l'utilisation de l'[API](https://github.com/Graitec-Group/advance-design-api) d'Advance Design**

**Une licence est également nécessaire afin de l'utiliser, et le logiciel AD2027 ou supérieur doit être installé**

Voir également [Advance Design Viewer](https://github.com/mooondark/ADViewer)

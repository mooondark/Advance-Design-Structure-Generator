# Changelog

## 2.1 - 2026-09-24
- Sections du formulaire encadrees, titre pose sur la bordure (suit le theme clair/sombre sans rechargement)
- Antenne : "Organiser en systemes" deplace dans la section Geometrie, comme pour le Portique
- Pied de page : liens vers le depot GitHub, le depot de l'API Graitec et le site Graitec (FR/UK/PL selon la langue)
- Le message de reussite ou d'echec disparait des qu'on change de structure, d'option ou de projet, ou qu'on arrete l'API
- Selecteur de structure n'est plus masque par la barre Streamlit ; espacement vertical reduit
- Hauteurs de haubans validees meme sans hauban, valeur `nan` rejetee
- Langue et structure active propres a chaque onglet (plus d'interference entre sessions)
- Une traduction avec un parametre inconnu ne fait plus planter l'application
- Tests : toute nouvelle structure est verifiee automatiquement (contrat, titre dans `[common]`)

## 2.0 - 2026-09-24
- Fusion de SteelFrameGenerator (1.32) et Antenna Generator (1.0) en une seule application, choix de la structure par liste deroulante
- Architecture modulaire : une structure = un module dans `structures/` + une ligne dans le registre
- Profils choisis par famille puis par nom, familles autorisees par element (catalogue Advance Design complet, 35 familles)
- Antenne : profils tubulaires circulaires, rectangulaires, carres et cornieres (CHSC, CHSH, RHSC, RHSH, SHSC, SHSH, L, Li)
- Materiaux S450 et S460 ajoutes
- Fichiers de langue FR/EN/PL fusionnes ; configuration unique `config.ini` (memorise la derniere structure)
- Interface compacte pour ecran 1920x1080 : etat de l'API porte par le bouton Demarrer/Arreter ; schema PNG de secours remplace par un message quand la geometrie est invalide

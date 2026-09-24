# Changelog

## 2.0 - 2026-09-24
- Fusion de SteelFrameGenerator (1.32) et Antenna Generator (1.0) en une seule application, choix de la structure par liste deroulante
- Architecture modulaire : une structure = un module dans `structures/` + une ligne dans le registre
- Profils choisis par famille puis par nom, familles autorisees par element (catalogue Advance Design complet, 35 familles)
- Antenne : profils tubulaires circulaires, rectangulaires, carres et cornieres (CHSC, CHSH, RHSC, RHSH, SHSC, SHSH, L, Li)
- Materiaux S450 et S460 ajoutes
- Fichiers de langue FR/EN/PL fusionnes ; configuration unique `config.ini` (memorise la derniere structure)
- Interface compacte pour ecran 1920x1080 : etat de l'API porte par le bouton Demarrer/Arreter ; schema PNG de secours remplace par un message quand la geometrie est invalide

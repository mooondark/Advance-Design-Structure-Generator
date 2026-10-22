# Changelog

## 2.5 - 2026-10-22
- API 1.27.1 et plus : licence et état du service vérifiés (GetStatus) avant toute génération ; en cas de problème, rien n'est généré et le message du serveur est affiché (traduit FR/EN/PL/ES/PT)
- Versions antérieures de l'API : pas de vérification, comportement inchangé
- L'enregistrement du projet à la fermeture est vérifié : un échec d'enregistrement est signalé au lieu d'afficher un succès
- En cas d'erreur pendant la génération, le projet est fermé sans enregistrer (CloseProjectWithoutSave) : un modèle partiel n'écrase plus le fichier
- Délai d'attente de la fermeture porté à 120 s (elle inclut désormais l'enregistrement)

## 2.4 - 2026-10-13
- Un nouveau fichier ne peut plus porter le nom d'un fichier existant (message traduit, aucune génération)
- Infobulle sur "Fichier existant" : les éléments sont ajoutés au projet, faire une copie avant de générer
- start.bat : Streamlit limité aux versions 1.64 à 1.x, plus de mise à jour automatique à chaque lancement
- Messages d'erreur de l'API traduits (FR/EN/PL/ES/PT)
- Plus d'attente inutile après un échec de connexion à l'API
- Code de l'aperçu 3D factorisé (core/util.py)

## 2.3 - 2026-09-30
- Nouvelles langues : espagnol (ES) et portugais européen (PT), avec les liens du site Graitec correspondants (/es/, /pt/)

## 2.2 - 2026-09-28
- Nouvelle structure "Portique béton" : bâtiment béton armé multi-étages (grille Nx x Ny, Ne étages de hauteurs identiques ou différentes), poteaux de façade / intérieurs, poutres de rive / intérieures excentrées vers le bas, dalle par niveau, appuis en pied
- Systèmes par étage (APPUI, POTEAU, VOILE, POUTRE, DALLE) avec la fonction Niveau activée
- Sections béton saisies par forme (carré, rectangulaire, circulaire) puis dimensions en cm
- Matériaux propres à chaque structure : aciers S235 à S460, bétons C20/25 à C40/50
- Correctif portique béton : un système par étage (Ne au lieu de Ne+1) ; chaque étage contient ses poteaux et le plancher en tête (poutres, dalle), niveau de Z_(k-1) à Z_k
- Correctif : changer de langue ne plante plus l'application (choix de structure, formes de section, type d'appui et de base gardent leur valeur)

## 2.1 - 2026-09-24
- Sections du formulaire encadrées, titre posé sur la bordure (suit le thème clair/sombre sans rechargement)
- Antenne : "Organiser en systèmes" déplacé dans la section Géométrie, comme pour le Portique
- Journal : les ":" de la synthèse restent alignés quelle que soit la longueur des libellés ; antenne, nombre d'éléments et de haubans affiché sur les lignes de section
- Pied de page : liens vers le dépôt GitHub, le dépôt de l'API Graitec et le site Graitec (FR/UK/PL selon la langue)
- Le message de réussite ou d'échec disparaît dès qu'on change de structure, d'option ou de projet, ou qu'on arrête l'API
- Sélecteur de structure n'est plus masqué par la barre Streamlit ; espacement vertical réduit
- Hauteurs de haubans validées même sans hauban, valeur `nan` rejetée
- Langue et structure active propres à chaque onglet (plus d'interférence entre sessions)
- Une traduction avec un paramètre inconnu ne fait plus planter l'application
- Tests : toute nouvelle structure est vérifiée automatiquement (contrat, titre dans `[common]`)

## 2.0 - 2026-09-24
- Fusion de SteelFrameGenerator (1.32) et Antenna Generator (1.0) en une seule application, choix de la structure par liste déroulante
- Architecture modulaire : une structure = un module dans `structures/` + une ligne dans le registre
- Profils choisis par famille puis par nom, familles autorisées par élément (catalogue Advance Design complet, 35 familles)
- Antenne : profils tubulaires circulaires, rectangulaires, carrés et cornières (CHSC, CHSH, RHSC, RHSH, SHSC, SHSH, L, Li)
- Matériaux S450 et S460 ajoutés
- Fichiers de langue FR/EN/PL fusionnés ; configuration unique `config.ini` (mémorise la dernière structure)
- Interface compacte pour écran 1920x1080 : état de l'API porté par le bouton Démarrer/Arrêter ; schéma PNG de secours remplacé par un message quand la géométrie est invalide

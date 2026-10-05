from structures import antenna, concrete_frame, convoyeur, steel_frame

# Ajouter une structure : creer structures/<nom>.py (voir le contrat dans la spec) et l'inscrire ici.
# Attribut facultatif VISIBLE_BY_DEFAULT = False : structure cachee tant que View_<Nom> n'est pas True.
STRUCTURES = {
    "steel_frame": steel_frame,
    "antenna": antenna,
    "concrete_frame": concrete_frame,
    "convoyeur": convoyeur,
}

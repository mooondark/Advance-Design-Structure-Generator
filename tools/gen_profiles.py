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
            if name.lower() != "name":
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

"""Geometrie pure du convoyeur : aucune dependance API ni Streamlit."""
import math

# Decalages normaux a la pente, mesures depuis la ligne des sommets de portiques (m).
V_CROSS, V_AXIS, V_BRACE = 0.03, 0.42, 0.76
OVERHANG = 0.09          # debord de la poutre principale au-dela du portique 3 (le long de la pente)
PENTE_DEBUT = 0.1235     # pente fixe de l'extremite de debut
REF_PENTE = 0.2755       # pente du modele d'origine : le gabarit de fin est pivote de l'ecart

I_TOP = "I17.5*1.1+17.5*0.75"
I_JUNCTION = "I17.5*0.8+9*0.5"

# Extremite de fin : gabarit fixe extrait de Transporteur-B2.fto, relatif au bout P14 de la poutre
# principale (Y = 0), a la pente de reference REF_PENTE. Colonne Y : "0", "W" (entraxe poutres) ou "-D" (debord). "St" = section choisie.
END_BARS = [
    ('Travée 1', 'Poutre transversale', 'St', 'sbeam', (0.1591, '-D', -0.3497), (0.1591, 'W', -0.3497)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.1591, '0', -0.3497), (0.0584, '0', 0.0161)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.1591, 'W', -0.3497), (0.0584, 'W', 0.0161)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.1721, '0', -0.0977), (0.0553, '0', 0.3265)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.1721, 'W', -0.0977), (0.0553, 'W', 0.3265)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.4228, '0', -0.0287), (0.3059, '0', 0.3955)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.4228, 'W', -0.0287), (0.3059, 'W', 0.3955)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.8386, '0', -0.0697), (0.7138, '0', 0.3834)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (0.8386, 'W', -0.0697), (0.7138, 'W', 0.3834)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (1.4846, '0', 0.1082), (1.3597, '0', 0.5613)),
    ('Extrémité fin', 'Filaire', 'RIGIDE', 'rigid', (1.4846, 'W', 0.1082), (1.3597, 'W', 0.5613)),
    ('Extrémité fin', 'Filaire', 'U53*0.8+16*0.8', 'sbeam', (1.4261, '0', 0.3203), (1.9521, '0', 0.4652)),
    ('Extrémité fin', 'Filaire', 'U53*0.8+16*0.8', 'sbeam', (1.4261, 'W', 0.3203), (1.9521, 'W', 0.4652)),
    ('Extrémité fin', 'Filaire', 'U53*0.8+16*0.8', 'sbeam', (1.9521, '0', 0.4652), (1.9521, 'W', 0.4652)),
    ('Extrémité fin', 'Filaire', 'U9.3*0.8+16*0.8', 'sbeam', (0.0553, '0', 0.3265), (0.3059, '0', 0.3955)),
    ('Extrémité fin', 'Filaire', 'U9.3*0.8+16*0.8', 'sbeam', (0.0553, 'W', 0.3265), (0.3059, 'W', 0.3955)),
    ('Extrémité fin', 'Filaire', 'I68*1+18*0.5', 'sbeam', (0.1349, '0', 0.0372), (0.0, '0', 0.0)),
    ('Extrémité fin', 'Filaire', 'U39.5*0.8+16*0.8', 'sbeam', (0.4228, '0', -0.0287), (0.1721, '0', -0.0977)),
    ('Extrémité fin', 'Filaire', 'U53*0.8+16*0.8', 'sbeam', (0.7802, '0', 0.1424), (0.4042, '0', 0.0388)),
    ('Extrémité fin', 'Filaire', 'L80x80x8', 'sbeam', (1.4846, '0', 0.1082), (0.8386, '0', -0.0697)),
    ('Extrémité fin', 'Filaire', 'L80x80x8', 'sbeam', (0.7138, '0', 0.3834), (1.3597, '0', 0.5613)),
    ('Extrémité fin', 'Filaire', 'U39.5*0.8+16*0.8', 'sbeam', (0.4228, 'W', -0.0287), (0.1721, 'W', -0.0977)),
    ('Extrémité fin', 'Filaire', 'U53*0.8+16*0.8', 'sbeam', (0.7802, 'W', 0.1424), (0.4042, 'W', 0.0388)),
    ('Extrémité fin', 'Filaire', 'L80x80x8', 'sbeam', (1.4846, 'W', 0.1082), (0.8386, 'W', -0.0697)),
    ('Extrémité fin', 'Filaire', 'L80x80x8', 'sbeam', (0.7138, 'W', 0.3834), (1.3597, 'W', 0.5613)),
    ('Extrémité fin', 'Filaire', 'I68*1+18*0.5', 'sbeam', (0.135, 'W', 0.0372), (0.0, 'W', 0.0)),
]


def _ykey(k, W, D):
    return {"0": 0.0, "W": W, "-D": -D}[k]


def heights(p):
    """Hauteurs (H1 saisie, H2 et H3 calculees) : sommets sur la ligne de pente issue de H1, pieds a Z = 0."""
    s = float(p["pente"]) / 100
    h1 = float(p["H1"])
    return h1, h1 + s * float(p["L1"]), h1 + s * (float(p["L1"]) + float(p["L2"]))


def build_model(p):
    """Retourne (bars, supports). bar = (systeme, nom, section, type, a, b) ; support = (systeme, pt)."""
    s = float(p["pente"]) / 100
    th = math.atan(s)
    c, sn = math.cos(th), math.sin(th)
    W, D = float(p["Em"]), float(p["debord"])
    yc = W / 2
    L1, L2 = float(p["L1"]), float(p["L2"])
    n1, n2, ntr = int(p["n1"]), int(p["n2"]), int(p["ntr"])
    N = n1 + n2
    z1 = float(p["H1"])                                 # sommet du portique 1

    def pt(u, v, y):
        return (u * c - v * sn, y, z1 + u * sn + v * c)

    u1, u2, u3 = 0.0, L1 / c, (L1 + L2) / c
    ys = (0.0, W)
    bars, supports = [], []

    def bar(sysname, name, sec, a, b, kind="sbeam"):
        bars.append((sysname, name, sec, kind, a, b))

    def lerp(a, b, t):
        return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

    # --- portiques
    top = {1: u1, 2: u2, 3: u3}
    E = {1: float(p["E1"]), 2: float(p["E2"]), 3: float(p["E3"])}
    base = {}
    for i in (1, 2, 3):
        for y, yb in zip(ys, (yc - E[i] / 2, yc + E[i] / 2)):
            t = pt(top[i], 0, y)
            base[i, y] = (t[0], yb, 0.0)
            supports.append((f"Portique {i}", base[i, y]))
        bar(f"Portique {i}", "Filaire", I_TOP, pt(top[i], 0, 0), pt(top[i], 0, W))

    def post(i, y, z):
        b, t = base[i, y], pt(top[i], 0, y)
        return lerp(b, t, (z - b[2]) / (t[2] - b[2]))

    def braced(i, zlow, n, trav_sec):
        zt = pt(top[i], 0, 0)[2]
        zs = [zlow + (zt - zlow) * k / n for k in range(n + 1)]
        for k in range(1, n):
            bar(f"Portique {i}", "Filaire", trav_sec, post(i, 0, zs[k]), post(i, W, zs[k]))
        for k in range(n):
            ctr = (post(i, 0, zs[k + 1])[0], yc, zs[k + 1])
            for y in ys:
                bar(f"Portique {i}", "Diagonale portique", p["Sd"], post(i, y, zs[k]), ctr)

    for y in ys:
        bar("Portique 1", "Poteau 1", p["S1"], base[1, y], pt(u1, 0, y))
        bar("Portique 2", "Poteau 2", p["S2"], base[2, y], pt(u2, 0, y))
    braced(2, base[2, 0][2], int(p["Ne2"]), "SHS60x4C")
    zj = base[3, 0][2] + float(p["Hs3"])
    for y in ys:
        j = post(3, y, zj)
        bar("Portique 3", "Poteau 3.1", p["S31"], base[3, y], j)
        bar("Portique 3", "Poteau 3.2", p["S32"], j, pt(u3, 0, y))
    bar("Portique 3", "Filaire", I_JUNCTION, post(3, 0, zj), post(3, W, zj))
    braced(3, zj, int(p["Ne3"]), p["Sx"])

    # --- poutres principales, traverses d'appui de poutre
    P14 = {y: pt(u3 + OVERHANG, V_AXIS, y) for y in ys}
    for y in ys:
        bar("Travée 1", "Poutre principale", p["Sm"], pt(u1, V_AXIS, y), pt(u2, V_AXIS, y))
        bar("Travée 2", "Poutre principale", p["Sm"], pt(u2, V_AXIS, y), P14[y])
    for u in (u1, u2, u3):
        bar("Travée 1", "Filaire", "SHS100x4C", pt(u, V_AXIS, 0), pt(u, V_AXIS, W))

    # --- noeuds de contreventement (ligne a V_BRACE)
    U = [u1 + (u2 - u1) * k / n1 for k in range(n1 + 1)] + [u2 + (u3 - u2) * k / n2 for k in range(1, n2 + 1)]

    # --- poutres transversales et poutre exterieure
    uc = [U[1 + (N - 2) * i // ntr] for i in range(ntr + 1)]   # sur des noeuds : (N - 2) multiple de ntr
    for u in uc:
        bar("Travée 1" if u < u2 - 1e-6 else "Travée 2", "Poutre transversale", p["St"],
            pt(u, V_CROSS, -D), pt(u, V_CROSS, W))
    for y in ys:
        bar("Travée 1", "Filaire", "CHS60.3x4C", base[1, y], pt(uc[0], V_CROSS, y))
    outer_end = pt(uc[-1], V_CROSS, -D)
    bar("Convoyeur", "Poutre extérieure", "L18.5*5*0.5", pt(uc[0], V_CROSS, -D), outer_end)

    # --- contreventement : transversales, diagonales en zigzag, bras rigides
    for k in range(N + 1):
        bar("Contreventement", "Contreventement", p["Sc"], pt(U[k], V_BRACE, 0), pt(U[k], V_BRACE, W))
    for k in range(N):
        ya, yb = (W, 0.0) if k % 2 == 0 else (0.0, W)
        bar("Contreventement", "Contreventement", p["Sc"], pt(U[k], V_BRACE, ya), pt(U[k + 1], V_BRACE, yb))
    for k in range(N + 1):
        vs = []
        if k in (0, n1, N):
            vs.append(0.0)
        if any(abs(u - U[k]) < 1e-3 for u in uc):
            vs.append(V_CROSS)
        if not vs:
            vs.append(V_AXIS)
        sysname, name = ("Rigides", "Rigide") if (k <= n1 or k == N) else ("Travée 2", "Filaire")
        for v in vs:
            for y in ys:
                bar(sysname, name, "RIGIDE", pt(U[k], v, y), pt(U[k], V_BRACE, y), "rigid")

    # --- extremite de debut (pente fixe)
    td = math.atan(PENTE_DEBUT)
    ld = float(p["Ldeb"])
    for y in ys:
        j1 = pt(u1, V_AXIS, y)
        a = (j1[0] - ld * math.cos(td), y, j1[2] - ld * math.sin(td))
        bar("Extrémité début", "Poutre P Début", p["Sdb"], a, j1)
    j1 = pt(u1, V_AXIS, 0)
    a = (j1[0] - ld * math.cos(td), 0.0, j1[2] - ld * math.sin(td))
    bar("Extrémité début", "Filaire", p["Sdu"], a, (a[0], W, a[2]))

    # --- extremite de fin : gabarit fixe pivote de (pente - REF_PENTE) autour de P14 et translate a P14,
    # puis prolongement de la poutre exterieure jusqu'a la derniere poutre transversale.
    o = P14[0]
    dth = th - math.atan(REF_PENTE)
    cd, sd = math.cos(dth), math.sin(dth)

    def end_pt(d):
        return (o[0] + d[0] * cd - d[2] * sd, _ykey(d[1], W, D), o[2] + d[0] * sd + d[2] * cd)

    for sysname, name, sec, kind, da, db in END_BARS:
        bar(sysname, name, p[sec] if sec == "St" else sec, end_pt(da), end_pt(db), kind)
    bar("Travée 2", "Filaire", "L18*5*0.5", outer_end, end_pt(END_BARS[0][4]))
    return bars, supports

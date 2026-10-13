"""Aides communes aux structures : apercu 3D filaire et lecture de listes de nombres."""


def lines3d(segs, color, width):
    """Trace Plotly 3D : un trait par segment ((x, y, z), (x, y, z)), sans relier les segments entre eux."""
    import plotly.graph_objects as go

    xs, ys, zs = [], [], []
    for a, b in segs:
        xs += [a[0], b[0], None]
        ys += [a[1], b[1], None]
        zs += [a[2], b[2], None]
    return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines",
                        line=dict(color=color, width=width), hoverinfo="skip")


def parse_floats(text):
    """'20, 40' -> [20.0, 40.0] ; ValueError si un element n'est pas un nombre."""
    return [float(x) for x in (text or "").split(",") if x.strip()]

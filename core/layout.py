"""Elements de mise en page communs : cadre de section, choix a libelles traduits."""
import streamlit as st


def section(key, icon, title):
    box = st.container(border=True, key=f"sec_{key}")
    box.markdown(f"{icon} **{title}**")
    return box


def choice(container, kind, label, options, state_key, format_func, on_change=None, **kw):
    """Selectbox ("select") ou segmented_control ("segmented") dont les libelles sont traduits.

    Streamlit memorise le libelle affiche, pas l'option : apres un changement de langue, l'ancien
    libelle ne correspond plus a aucune option et Streamlit renvoie le texte brut. La cle du widget
    inclut donc la langue ; la valeur de reference reste dans st.session_state[state_key].
    """
    ss = st.session_state
    wkey = f"{state_key.replace('.', ':')}@{ss['settings.lang']}"

    def _sync():
        ss[state_key] = ss[wkey]
        if on_change:
            on_change()

    if kind == "segmented":
        container.segmented_control(label, options, default=ss[state_key], format_func=format_func,
                                    key=wkey, required=True, on_change=_sync, **kw)
    else:
        container.selectbox(label, options, index=list(options).index(ss[state_key]), format_func=format_func,
                            key=wkey, on_change=_sync, **kw)
    return ss[state_key]

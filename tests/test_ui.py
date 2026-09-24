import threading

import streamlit as st

from core import i18n, ui


def test_browse_callback_translates_in_fresh_thread(monkeypatch):
    # Un callback Streamlit s'execute dans le thread d'un nouveau run, avant que main() charge la langue.
    titles = []
    monkeypatch.setattr(ui, "native_pick", lambda save, initial="": titles.append(i18n.T("browse_title_fto")) or "")
    st.session_state["settings.lang"] = "fr"
    st.session_state["project.new"] = True
    st.session_state["project.name"] = "p"

    t = threading.Thread(target=ui._browse)
    t.start()
    t.join()
    assert titles and not titles[0].startswith("[")

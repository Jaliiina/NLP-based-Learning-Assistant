import streamlit as st

from aid_integrated.nlp.app import tfidf_page


def render() -> None:
    if not (isinstance(st.session_state.get("shared_text"), str) and st.session_state["shared_text"].strip()):
        seed = st.session_state.get("campus_raw_text_for_nlp", "")
        if isinstance(seed, str) and seed.strip():
            st.session_state["shared_text"] = seed

    tfidf_page()

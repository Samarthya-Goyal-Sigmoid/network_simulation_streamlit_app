# https://github.com/victoryhb/streamlit-option-menu
from streamlit_option_menu import option_menu
import streamlit as st
from PIL import Image


def render_sidebar():
    with st.sidebar:
        logo = Image.open("logo/lift_logo.png")
        _, c1, _ = st.columns([0.2, 0.8, 0.2])
        with c1:
            st.image(logo, width=200)
        selected = option_menu(
            menu_title=None,
            options=["Home", "Chat Sessions", "Settings"],
            icons=["house", "chat", "gear"],
            default_index=0,
            orientation="vertical",
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "#FFFFFF",
                },
                "nav-link": {
                    "text-align": "left",
                    "margin": "8px",
                    "--hover-color": "#eee",
                    "border-radius": "5em",
                },
                "nav-link-selected": {
                    "background-color": "#FDE5E5",
                    "color": "#DA1E18",
                    "border-radius": "5em",
                    "border": "1px solid #DA1E18",
                },
            },
        )
        return selected

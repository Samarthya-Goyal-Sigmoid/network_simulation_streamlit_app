# https://github.com/victoryhb/streamlit-option-menu
from streamlit_option_menu import option_menu
import streamlit as st
from PIL import Image
import pandas as pd

# Import files
from .session_state_manager import init_session_state

init_session_state()
from .ui_helpers import get_horizontal_line


def render_sidebar():
    with st.sidebar:
        col1, col2 = st.columns([0.4, 0.6])
        with col1:
            st.image("logo/sigmoid_logo.png", width=300)
        with col2:
            st.image("logo/nestle_logo.png", width=300)
        get_horizontal_line(color="#E30A13")
        st.markdown("")
        selected = option_menu(
            menu_title=None,
            options=["Network Design", "Network Visualization", "Simulate Scenario", "Scenario Comparison"],
            icons=["diagram-3", "graph-up", "play", "columns-gap"],
            default_index=0,
            orientation="vertical",
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "#FFFFFF",
                },
                "nav-link-selected": {
                    "text-align": "left",
                    "margin": "8px",
                    "color": "rgb(218, 30, 24)",
                    "--hover-color": "#eee",
                    "background-color": "rgb(253, 229, 229)",
                    "border-radius": "5em",
                    "border" : "1px solid rgb(218, 30, 24)",
                },
                "nav-link": {
                    "text-align": "left",
                    "margin": "8px",
                    "--hover-color": "#eee",
                    "border-radius": "5em",
                },
            },
        )
        get_horizontal_line(color="#E30A13")
        return selected

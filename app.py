"""
Created on Fri Aug 8 2025

@author: Nitish Sawant
"""

# Steps to run the app
# streamlit run app.py

# Import Libraries
import warnings

warnings.filterwarnings("ignore")
import streamlit as st

import pandas as pd
import os
import yaml
import sys

sys.path.append("src")

# Page config
st.set_page_config(
    page_title="Supply Chain Network Simulator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import files
from components.session_state_manager import init_session_state

init_session_state()

from components.sidebar import render_sidebar
from components.home_tab import render_home
from components.settings_tab import render_settings_tab

# New tab imports
from components.network_design_tab import render_network_design
from components.network_visualization_tab import render_network_visualization
from components.simulate_scenario_tab import render_simulate_scenario
from components.scenario_comparison_tab import render_scenario_comparison

# Load custom CSS
with open("style/custom.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

selected_tab = render_sidebar()

# Routing
if selected_tab == "Home":
    render_home()
elif selected_tab == "Settings":
    render_settings_tab()
elif selected_tab == "Network Design":
    render_network_design()
elif selected_tab == "Network Visualization":
    render_network_visualization()
elif selected_tab == "Simulate Scenario":
    render_simulate_scenario()
elif selected_tab == "Scenario Comparison":
    render_scenario_comparison()
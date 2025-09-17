# Import libraries
import streamlit as st
import yaml
import os
import pickle
import sys
from datetime import datetime
import pandas as pd

from src.helpers import preprocess_expense_data, preprocess_budget_data
from components.ui_helpers import get_default_network_tables


def init_session_state():
    # Session state
    if "backend_expense_data" not in st.session_state:
        df_expenses = preprocess_expense_data(f"src/data/Expenses_RB.csv")
        st.session_state["backend_expense_data"] = df_expenses.to_dict("records")
    if "backend_budget_data" not in st.session_state:
        df_budget = preprocess_budget_data(f"src/data/Budget_RB.csv")
        st.session_state["backend_budget_data"] = df_budget.to_dict("records")
    if "expense_data" not in st.session_state:
        st.session_state["expense_data"] = []
    if "budget_data" not in st.session_state:
        st.session_state["budget_data"] = []
    if "expense_data_file_name" not in st.session_state:
        st.session_state["expense_data_file_name"] = None
    if "budget_data_file_name" not in st.session_state:
        st.session_state["budget_data_file_name"] = None
    if "show_chat_session" not in st.session_state:
        st.session_state["show_chat_session"] = False
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "agent_obj" not in st.session_state:
        st.session_state["agent_obj"] = None
    if "use_backend_data" not in st.session_state:
        st.session_state["use_backend_data"] = True
    if "model_name" not in st.session_state:
        st.session_state["model_name"] = "gpt-4o"
    if "plot_path" not in st.session_state:
        st.session_state["plot_path"] = "src/streamlit_plots"
    # Open AI key
    if "open_ai_key" not in st.session_state:
        st.session_state["open_ai_key"] = ""



    # --- Network Design Tab Session States ---
    if "tables" not in st.session_state:
        st.session_state["tables"] = get_default_network_tables().copy()
    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "Factory Level"
    if "file_uploaded_once" not in st.session_state:
        st.session_state["file_uploaded_once"] = False
    if "show_download_button" not in st.session_state:
        st.session_state["show_download_button"] = False
    if "action" not in st.session_state:
        st.session_state["action"] = None
    if "uploaded_sheets" not in st.session_state:
        st.session_state["uploaded_sheets"] = []

    # Initialize editor_buffer_{tab_name} keys for all default tabs
    for tab_name in st.session_state["tables"].keys():
        buffer_key = f"editor_buffer_{tab_name.replace(' ', '_')}"
        if buffer_key not in st.session_state:
            st.session_state[buffer_key] = st.session_state["tables"][tab_name].copy()


    for key in list(st.session_state.keys()):
        if key.startswith("editor_buffer_") or key.endswith("_table"):
            del st.session_state[key]
    for key in ["file_uploaded_once", "action", "uploaded_sheets", "active_tab"]:
        if key in st.session_state:
            del st.session_state[key]

    st.session_state["tables"] = get_default_network_tables().copy()
    st.session_state["file_uploaded_once"] = False
    st.session_state["active_tab"] = "Factory Level"

    for tab_name in st.session_state["tables"].keys():
        buffer_key = f"editor_buffer_{tab_name.replace(' ', '_')}"
        st.session_state[buffer_key] = st.session_state["tables"][tab_name].copy()
# Import libraries
import streamlit as st
import yaml
import os
import pickle
import sys
from datetime import datetime
import pandas as pd
from components.ui_helpers import get_default_network_tables

def init_session_state():
    # Session state
    # if "backend_expense_data" not in st.session_state:
    #     df_expenses = preprocess_expense_data(f"src/data/Expenses_RB.csv")
    #     st.session_state["backend_expense_data"] = df_expenses.to_dict("records")
    # if "backend_budget_data" not in st.session_state:
    #     df_budget = preprocess_budget_data(f"src/data/Budget_RB.csv")
    #     st.session_state["backend_budget_data"] = df_budget.to_dict("records")
    # if "expense_data" not in st.session_state:
    #     st.session_state["expense_data"] = []
    # if "budget_data" not in st.session_state:
    #     st.session_state["budget_data"] = []
    # if "expense_data_file_name" not in st.session_state:
    #     st.session_state["expense_data_file_name"] = None
    # if "budget_data_file_name" not in st.session_state:
    #     st.session_state["budget_data_file_name"] = None
    # if "show_chat_session" not in st.session_state:
    #     st.session_state["show_chat_session"] = False
    # if "messages" not in st.session_state:
    #     st.session_state["messages"] = []
    # if "agent_obj" not in st.session_state:
    #     st.session_state["agent_obj"] = None
    # if "use_backend_data" not in st.session_state:
    #     st.session_state["use_backend_data"] = True
    # if "model_name" not in st.session_state:
    #     st.session_state["model_name"] = "gpt-4o"
    # if "plot_path" not in st.session_state:
    #     st.session_state["plot_path"] = "src/streamlit_plots"
    # # Open AI key
    # if "open_ai_key" not in st.session_state:
    #     st.session_state["open_ai_key"] = ""


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
    if "_main_upload_md5" not in st.session_state:
        st.session_state["_main_upload_md5"] = None

def reset_session_state():
    st.session_state["tables"] = get_default_network_tables().copy()
    st.session_state["active_tab"] = "Factory Level"
    st.session_state["file_uploaded_once"] = False
    st.session_state["show_download_button"] = False
    st.session_state["action"] = None
    st.session_state["uploaded_sheets"] = []
    st.session_state["_main_upload_md5"] = None
    # Also clear editor keys so UI doesn’t resurrect old rows
    for key in list(st.session_state.keys()):
        if key.startswith("editor_") or key.startswith("__md5_"):
            del st.session_state[key]
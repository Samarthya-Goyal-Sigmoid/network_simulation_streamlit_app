# Import libraries
import streamlit as st
import yaml
import os
import pickle
import sys
from datetime import datetime
import pandas as pd


def init_session_state():
    # Session state
    if "backend_expense_data" not in st.session_state:
        st.session_state["backend_expense_data"] = pd.read_csv(
            f"src/data/Expense.csv"
        ).to_dict("records")
    if "backend_budget_data" not in st.session_state:
        st.session_state["backend_budget_data"] = pd.read_csv(
            f"src/data/Budget.csv"
        ).to_dict("records")
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
        st.session_state["use_backend_data"] = False
    if "model_name" not in st.session_state:
        st.session_state["model_name"] = "gpt-4o"

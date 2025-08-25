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
        df_budget = pd.read_csv(f"src/data/Budget.csv")
        for col in ["2023 - Budget", "2024 - Budget"]:
            if col in df_budget.columns:
                df_budget[col] = (
                    df_budget[col].str.replace(",", "", regex=False).astype(int)
                )
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
        st.session_state["use_backend_data"] = False
    if "model_name" not in st.session_state:
        st.session_state["model_name"] = "gpt-4o"

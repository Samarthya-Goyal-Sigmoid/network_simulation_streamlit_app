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
        df_expenses = pd.read_csv(
            f"src/data/Expenses_RB.csv",
            usecols=[
                "Region",
                "Country",
                "Category",
                "Brand",
                "Year",
                "Time Month",
                "Tier 1",
                "Tier 2",
                "Tier 3",
                "Expense Status",
                "Pending At",
                "Expense Logged by (NS)",
                "Audit Status",
                "Audit Comments",
                "Pep Share (USD)",
                "Bottler Share (USD)",
                "Total Expense (USD)",
            ],
        )
        # Preprocessing
        # Convert to integer
        for col in ["Pep Share (USD)", "Bottler Share (USD)", "Total Expense (USD)"]:
            df_expenses[col] = df_expenses[col].fillna(0)
            df_expenses[col] = df_expenses[col].astype(int)
        # Convert to title case format
        for col in ["Expense Status", "Audit Status"]:
            df_expenses[col] = df_expenses[col].str.title()
        # Renaming columns
        df_expenses = df_expenses.rename(
            columns={
                "Time Month": "Month",
                "Expense Logged by (NS)": "Expense Logged by",
                "Pep Share (USD)": "Pep Expense",
                "Bottler Share (USD)": "Bottler Expense",
                "Total Expense (USD)": "Total Expense",
            }
        )
        st.session_state["backend_expense_data"] = df_expenses.to_dict("records")
    if "backend_budget_data" not in st.session_state:
        df_budget = pd.read_csv(
            f"src/data/Budget_RB.csv",
            usecols=[
                "Region",
                "Country",
                "Year",
                "Category",
                "Brand",
                "Tier 1",
                "Tier 2",
                "Tier 3",
                "Pep Budget",
                "Bottler Budget",
                "Budget",
            ],
        )
        # Preprocessing
        for col in ["Pep Budget", "Bottler Budget", "Budget"]:
            df_budget[col] = df_budget[col].fillna(0)
            df_budget[col] = df_budget[col].astype(int)
        # Renaming columns
        df_budget = df_budget.rename(columns={"Budget": "Total Budget"})
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
        with open("config.yaml", "r") as f:
            llm_keys = yaml.safe_load(f)
        if llm_keys["open_ai"].strip() != "":
            os.environ["OPENAI_API_KEY"] = llm_keys["open_ai"]
        st.session_state["open_ai_key"] = llm_keys["open_ai"]

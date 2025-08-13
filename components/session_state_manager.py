# Import libraries
import streamlit as st
import yaml
import os
import pickle
import sys
from datetime import datetime


def init_session_state():
    # Session state
    if "historical_expenses_data" not in st.session_state:
        st.session_state["historical_expenses_data"] = []
    if "current_year_expenses_data" not in st.session_state:
        st.session_state["current_year_expenses_data"] = []
    if "budget_data" not in st.session_state:
        st.session_state["budget_data"] = []
    if "historical_expenses_data_file_name" not in st.session_state:
        st.session_state["historical_expenses_data_file_name"] = None
    if "current_year_expenses_data_file_name" not in st.session_state:
        st.session_state["current_year_expenses_data_file_name"] = None
    if "budget_data_file_name" not in st.session_state:
        st.session_state["budget_data_file_name"] = None
    if "show_chat_session" not in st.session_state:
        st.session_state["show_chat_session"] = False
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "agent_obj" not in st.session_state:
        st.session_state["agent_obj"] = None

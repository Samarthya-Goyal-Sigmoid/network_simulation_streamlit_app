import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_extras.stylable_container import stylable_container

# Import files
from .session_state_manager import init_session_state
from .read_files import parse_uploaded_file

init_session_state()

from .ui_helpers import (
    container_css_styles,
    get_horizontal_line,
    add_text,
    success_box,
    error_box,
)

text_color = "#E30A13"
horizontal_line_color = "#E30A13"


def render_home():
    with stylable_container(
        key="home_title",
        css_styles=container_css_styles,
    ):

        c1, _, c2 = st.columns([0.4, 0.4, 0.1], vertical_alignment="center")
        with c1:
            add_text(text="Generative AI Assistant", text_color=text_color, size=2)
        with c2:
            logo = Image.open("logo/sigmoid_logo.png")
            # Center the image using HTML
            st.image(logo, width=100)  # You can adjust width if needed

        st.markdown("📊 **Upload datasets and ask questions with context-aware chat!**")

    # Container css styles
    container_home_css_styles = """
        {
            background-color: #FFFFFF;
            padding-top: 1em;
            padding-right: 1em;
            padding-bottom: 1em;
            padding-left: 1em;
            border-radius: 0.5em;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            max-height: 520px;
            overflow-y: auto; /* Scroll if content exceeds */
        }
    """
    with stylable_container(
        key="home_upload",
        css_styles=container_home_css_styles,
    ):
        add_text(text="Upload Data", text_color=text_color, size=5)
        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            add_text(text="Expenses", text_color="black", size=6)
            expense_uploaded_file = st.file_uploader(
                "**Upload datasets**",
                type=["csv", "xlsx"],
                accept_multiple_files=False,
                label_visibility="collapsed",
                key="upload_expenses",
            )
        with c2:
            add_text(text="Budget Data", text_color="black", size=6)
            budget_uploaded_file = st.file_uploader(
                "**Upload datasets**",
                type=["csv", "xlsx"],
                accept_multiple_files=False,
                label_visibility="collapsed",
                key="upload_budget",
            )

        if expense_uploaded_file:
            get_horizontal_line(horizontal_line_color)
            # for uploaded_file in uploaded_files:
            st.markdown(f"##### 📄 File: {expense_uploaded_file.name}")
            status, message, df = parse_uploaded_file(
                expense_uploaded_file,
                required_cols=[
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
            if status == "error":
                error_box(message)
            elif status == "success":
                success_box(message)
                # Preprocessing
                for col in [
                    "Pep Share (USD)",
                    "Bottler Share (USD)",
                    "Total Expense (USD)",
                ]:
                    df[col] = df[col].fillna(0)
                    df[col] = df[col].astype(int)
                for col in ["Expense Status", "Audit Status"]:
                    df[col] = df[col].str.title()
                # Renaming columns
                df = df.rename(
                    columns={
                        "Time Month": "Month",
                        "Expense Logged by (NS)": "Expense Logged by",
                        "Pep Share (USD)": "Pep Expense",
                        "Bottler Share (USD)": "Bottler Expense",
                        "Total Expense (USD)": "Total Expense",
                    }
                )
                st.session_state["expense_data"] = df.to_dict("records")
                st.session_state["expense_data_file_name"] = expense_uploaded_file.name

        if budget_uploaded_file:
            get_horizontal_line(horizontal_line_color)
            # for uploaded_file in uploaded_files:
            st.markdown(f"##### 📄 File: {budget_uploaded_file.name}")
            status, message, df = parse_uploaded_file(
                budget_uploaded_file,
                required_cols=[
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
            if status == "error":
                error_box(message)
            elif status == "success":
                success_box(message)
                # Preprocessing
                for col in ["Pep Budget", "Bottler Budget", "Budget"]:
                    df[col] = df[col].fillna(0)
                    df[col] = df[col].astype(int)
                # Renaming columns
                df = df.rename(columns={"Budget": "Total Budget"})
                st.session_state["budget_data"] = df.to_dict("records")
                st.session_state["budget_data_file_name"] = budget_uploaded_file.name

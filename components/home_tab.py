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

    with stylable_container(
        key="home_upload",
        css_styles=container_css_styles,
    ):
        add_text(text="Upload Data", text_color=text_color, size=5)
        st.markdown("")
        c1, c2, c3 = st.columns(3)
        with c1:
            add_text(text="Historical Expenses", text_color="black", size=6)
            expense_uploaded_file = st.file_uploader(
                "**Upload datasets**",
                type=["csv", "xlsx"],
                accept_multiple_files=False,
                label_visibility="collapsed",
                key="upload_historical_expenses",
            )
        with c2:
            add_text(text="Current Year Expenses", text_color="black", size=6)
            cy_expenses_uploaded_file = st.file_uploader(
                "**Upload datasets**",
                type=["csv", "xlsx"],
                accept_multiple_files=False,
                label_visibility="collapsed",
                key="upload_cy_expenses",
            )
        with c3:
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
                    "Country",
                    "Year",
                    "Month",
                    "Category",
                    "Brand",
                    "Data Type",
                    "Tier 1",
                    "Tier 2",
                    "Tier 3",
                    "Expense",
                ],
            )
            if status == "error":
                error_box(message)
            elif status == "success":
                success_box(message)
                st.session_state["historical_expenses_data"] = df.to_dict("records")
                st.session_state["historical_expenses_data_file_name"] = (
                    expense_uploaded_file.name
                )

        if cy_expenses_uploaded_file:
            get_horizontal_line(horizontal_line_color)
            # for uploaded_file in uploaded_files:
            st.markdown(f"##### 📄 File: {cy_expenses_uploaded_file.name}")
            status, message, df = parse_uploaded_file(
                cy_expenses_uploaded_file,
                required_cols=[
                    "Country",
                    "Year",
                    "Month",
                    "Category",
                    "Brand",
                    "Tier 1",
                    "Tier 2",
                    "Tier 3",
                    "Description",
                    "Expense",
                    "Status",
                ],
            )
            if status == "error":
                error_box(message)
            elif status == "success":
                success_box(message)
                st.session_state["current_year_expenses_data"] = df.to_dict("records")
                st.session_state["current_year_expenses_data_file_name"] = (
                    cy_expenses_uploaded_file.name
                )

        if budget_uploaded_file:
            get_horizontal_line(horizontal_line_color)
            # for uploaded_file in uploaded_files:
            st.markdown(f"##### 📄 File: {budget_uploaded_file.name}")
            status, message, df = parse_uploaded_file(
                budget_uploaded_file,
                required_cols=[
                    "Country",
                    "Tier 1",
                    "Tier 2",
                    "Tier 3",
                    "2023 - Split (%)",
                    "2024 - Split (%)",
                    "2023 - Budget",
                    "2024 - Budget",
                ],
            )
            if status == "error":
                error_box(message)
            elif status == "success":
                success_box(message)
                st.session_state["budget_data"] = df.to_dict("records")
                st.session_state["budget_data_file_name"] = budget_uploaded_file.name

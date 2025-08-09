import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_extras.stylable_container import stylable_container
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
            add_text(text="AI Assistant", text_color=text_color, size=2)
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
        uploaded_files = st.file_uploader(
            "**Upload datasets**",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        # with c2:
        if uploaded_files:
            get_horizontal_line(horizontal_line_color)
            for uploaded_file in uploaded_files:
                st.markdown(f"##### 📄 File: {uploaded_file.name}")
                try:
                    # Detect file type by extension
                    file_name = uploaded_file.name.lower()

                    if file_name.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                    elif file_name.endswith((".xlsx", ".xls")):
                        df = pd.read_excel(uploaded_file)
                    else:
                        error_box(f"Unsupported file format.")
                        continue

                    # Validate columns
                    # Check for missing columns
                    missing_cols = ["Column A", "Column B", "Column C", "Column D"]

                    if missing_cols:
                        error_box(
                            f"Missing required columns: {', '.join(missing_cols)}"
                        )
                    else:
                        success_box(
                            "All required columns are present. Proceed to 'Chat Sessions' tab!"
                        )
                except Exception as e:
                    error_box(f"Error reading the file: {e}")

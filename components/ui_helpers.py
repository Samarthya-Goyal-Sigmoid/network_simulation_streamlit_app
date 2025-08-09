import streamlit as st


def success_box(message):
    st.success(f"✅ {message}")


def error_box(message):
    st.error(f"❌ {message}")


# Container css styles
container_css_styles = """
    {
        background-color: #FFFFFF;
        padding-top: 1em;
        padding-right: 1em;
        padding-bottom: 1em;
        padding-left: 1em;
        border-radius: 0.5em;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
"""


def get_horizontal_line(color):
    st.markdown(
        f"<hr style='border: 0.5px solid {color}; margin: 0px 0; padding: 0;'>",
        unsafe_allow_html=True,
    )


def add_text(text, text_color, size):
    st.markdown(
        f"<h{size} style='color:{text_color};'>{text}</h{size}>",
        unsafe_allow_html=True,
    )

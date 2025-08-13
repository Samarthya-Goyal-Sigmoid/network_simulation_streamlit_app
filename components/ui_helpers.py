import streamlit as st
import os
import base64


def success_box(message):
    st.success(f"✅ {message}")


def error_box(message):
    st.error(f"❌ {message}")


def warning_box(message):
    st.warning(f"⚠️ {message}")


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

chat_avatars = {
    "supervisor": "https://api.dicebear.com/7.x/initials/svg?seed=SA&backgroundColor=3366CC&fontSize=40",
    "Budget_Agent": "https://api.dicebear.com/7.x/initials/svg?seed=BA&backgroundColor=DC3912&fontSize=40",
    "Historical_Expense_Agent": "https://api.dicebear.com/7.x/initials/svg?seed=HE&backgroundColor=FF9900&fontSize=40",
    "CY_Expense_Agent": "https://api.dicebear.com/7.x/initials/svg?seed=CE&backgroundColor=109618&fontSize=40&color=ffffff",
    "SELF_RESPONSE": "https://api.dicebear.com/7.x/initials/svg?seed=SR&backgroundColor=990099&fontSize=40&color=ffffff",
    "User": "https://api.dicebear.com/7.x/initials/svg?seed=U&backgroundColor=0099C6&fontSize=40&color=ffffff",
    "Budget Agent": "https://api.dicebear.com/7.x/initials/svg?seed=BA&backgroundColor=DC3912&fontSize=40",
    "Historical Expense Agent": "https://api.dicebear.com/7.x/initials/svg?seed=HE&backgroundColor=FF9900&fontSize=40",
    "CY Expense Agent": "https://api.dicebear.com/7.x/initials/svg?seed=CE&backgroundColor=109618&fontSize=40&color=ffffff",
}


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


def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def display_saved_plot(plot_path: str):
    bg_color: str = "#f0f2f6"
    padding: str = "0.75em"
    border_radius: str = "0.75em"
    if os.path.exists(plot_path):
        st.markdown(
            f"""
            <style>
                .image-container {{
                    display: flex;
                    justify-content: center;
                }}
            </style>
            <div class="image-container">
                <img src="data:image/png;base64,{get_base64_image(plot_path)}" style="width:650px; height:auto;">
            </div>
            """,
            unsafe_allow_html=True,
        )

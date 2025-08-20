import streamlit as st
import os
import base64
import matplotlib.colors as mcolors


# Convert messages to plain text
def messages_to_text(messages):
    lines = []
    for msg in messages:
        if msg["figure_path"]:
            lines.append(
                f"{msg['role'].capitalize()} ({msg['agent'].capitalize()}): {msg['content']} \nFigure path: {msg['figure_path']}"
            )
        else:
            lines.append(
                f"{msg['role'].capitalize()} ({msg['agent'].capitalize()}): {msg['content']}"
            )
    return "\n\n".join(lines)


def success_box(message):
    st.success(f"✅ {message}")


def error_box(message):
    st.error(f"❌ {message}")


def warning_box(message):
    st.warning(f"⚠️ {message}")


def lighten_color(color, amount=0.3):
    """
    Lightens the given color by mixing it with white.
    amount=0 → no change, amount=1 → white
    """
    try:
        c = mcolors.cnames[color]  # Convert color name to hex
    except:
        c = color
    c = mcolors.to_rgb(c)
    return mcolors.to_hex([1 - (1 - x) * (1 - amount) for x in c])


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

lighten_amount = 0.92
chat_avatars_color_bg = {
    "Assistant": lighten_color("#049BE5", lighten_amount),
    "Error": lighten_color("#E53835", lighten_amount),
    "supervisor": lighten_color("#3366CC", lighten_amount),
    "Budget_Agent": lighten_color("#DC3912", lighten_amount),
    "Historical_Expense_Agent": lighten_color("#FF9900", lighten_amount),
    "CY_Expense_Agent": lighten_color("#109618", lighten_amount),
    "SELF_RESPONSE": lighten_color("#990099", lighten_amount),
    "User": lighten_color("#0099C6", lighten_amount),
    "Budget Agent": lighten_color("#DC3912", lighten_amount),
    "Historical Expense Agent": lighten_color("#FF9900", lighten_amount),
    "CY Expense Agent": lighten_color("#109618", lighten_amount),
}
chat_avatars = {}
for chat in [
    "Assistant",
    "Error",
    "supervisor",
    "Budget_Agent",
    "Historical_Expense_Agent",
    "CY_Expense_Agent",
    "SELF_RESPONSE",
    "User",
    "Budget Agent",
    "Historical Expense Agent",
    "CY Expense Agent",
]:
    chat_avatars[chat] = f"logo/avatars/{chat}.svg"


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


def display_saved_plot(plot_path: str, bg_color="#f0f2f6"):
    if os.path.exists(plot_path):
        st.markdown(
            f"""
            <style>
                .image-container {{
                    display: flex;
                    justify-content: center;
                    padding-bottom: 0.75em;
                    border-radius: 0em 0em 0.5em 0.5em;
                    background-color: {bg_color}
                }}
            </style>
            <div class="image-container">
                <img src="data:image/png;base64,{get_base64_image(plot_path)}" style="width:650px; height:auto;">
            </div>
            """,
            unsafe_allow_html=True,
        )

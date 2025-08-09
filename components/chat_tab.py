import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from .ui_helpers import container_css_styles, get_horizontal_line, add_text
import random

text_color = "#E30A13"
chat_container_css_styles = """
    {
        background-color: #FFFFFF;
        padding-top: 1em;
        padding-right: 1em;
        padding-bottom: 1em;
        padding-left: 1em;
        border-radius: 0.5em;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        height: 530px; /* Fixed height */
        overflow-y: auto; /* Scroll if content exceeds */
    }
"""


def render_chat_tab():
    # Initial states
    if "show_chat_session" not in st.session_state:
        st.session_state["show_chat_session"] = False
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    # Header container
    with stylable_container(
        key="chat_title",
        css_styles=container_css_styles,
    ):
        c1, c2, _, c3 = st.columns([0.20, 0.45, 0.15, 0.2], vertical_alignment="top")
        with c1:
            add_text(text="Start Chat Session:", text_color=text_color, size=5)
        with c2:
            select_options = st.multiselect(
                "Select the dataset(s)",
                [
                    "Green",
                    "Yellow",
                    "Red",
                    "Blue",
                    "Green2",
                    "Yellow2",
                    "Red2",
                    "Blue2",
                ],
                default=["Yellow", "Red"],
                max_selections=3,
                placeholder="Select dataset",
                label_visibility="collapsed",
            )
            st.markdown("")
        with c3:
            chat_button = st.button("Create Chat Session", icon=":material/add_circle:")
            # If chat button is hit
            if chat_button:
                st.session_state["messages"] = []
                st.session_state["show_chat_session"] = True
    # Chat session container
    if st.session_state["show_chat_session"]:
        with stylable_container(
            key="chat_session",
            css_styles=chat_container_css_styles,
        ):
            if len(st.session_state["messages"]) == 0:
                st.markdown("")

            for message in st.session_state["messages"]:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                elif message["role"] == "assistant":
                    with st.chat_message("assistant"):
                        st.write(message["content"])

    if st.session_state["show_chat_session"]:
        with stylable_container(
            key="chat_query_session",
            css_styles=container_css_styles,
        ):
            if prompt := st.chat_input(
                "I'm your assistant. Ask me whenever you're ready!"
            ):
                # Add user input to message list
                message = [{"role": "user", "content": prompt}]
                st.session_state["messages"] = message + st.session_state["messages"]
                # Answer from bot
                # Sample sentences
                sentences = [
                    "The quick brown fox jumps over the lazy dog.",
                    "Artificial intelligence is transforming the world.",
                    "She enjoys reading science fiction novels in her free time.",
                    "The sunset painted the sky in hues of orange and pink.",
                    "A sudden storm caught the hikers off guard.",
                    "Data is the new oil in today's digital economy.",
                    "He brewed a cup of coffee and sat by the window.",
                    "They launched the new product with great anticipation.",
                    "The experiment yielded surprising results.",
                    "Technology continues to evolve at a rapid pace.",
                ]

                def generate_random_text():
                    num_sentences = random.choice([1, 2])
                    return " ".join(random.sample(sentences, num_sentences))

                # Answer from bot
                bot_answer = generate_random_text()
                message = [{"role": "assistant", "content": bot_answer}]
                st.session_state["messages"] = message + st.session_state["messages"]
                st.rerun()
            st.markdown("")

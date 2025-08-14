import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import random
import os
import pandas as pd
from langchain.schema import HumanMessage
from langgraph.graph.message import add_messages

# Import files
from .session_state_manager import init_session_state

init_session_state()
from .ui_helpers import (
    warning_box,
    chat_avatars,
    display_saved_plot,
    add_text,
    container_css_styles,
    chat_avatars_color_bg,
    messages_to_text,
)
from src.main_file import AgentLift

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
    # Header container
    with stylable_container(
        key="chat_title",
        css_styles=container_css_styles,
    ):
        c1, c2, _, c3, c4 = st.columns(
            [0.2, 0.45, 0.07, 0.18, 0.05], vertical_alignment="top"
        )
        with c1:
            add_text(text="Start Chat Session:", text_color=text_color, size=5)
        with c2:
            if st.session_state["use_backend_data"] == True:
                possible_options = ["Historical Expense", "CY Expense", "Budget"]
                select_options = st.multiselect(
                    "Select the dataset(s)",
                    possible_options,
                    default=possible_options,
                    placeholder="Select dataset",
                    label_visibility="collapsed",
                )
            else:
                possible_options = []
                if st.session_state["historical_expenses_data_file_name"]:
                    possible_options.append("Historical Expense")
                if st.session_state["current_year_expenses_data_file_name"]:
                    possible_options.append("CY Expense")
                if st.session_state["budget_data_file_name"]:
                    possible_options.append("Budget")
                select_options = st.multiselect(
                    "Select the dataset(s)",
                    possible_options,
                    default=possible_options,
                    placeholder="Select dataset",
                    label_visibility="collapsed",
                )
            st.markdown("")
        with c3:
            chat_button = st.button("Create Chat Session", icon=":material/add_circle:")
            # If chat button is hit
            if chat_button:
                # Reset session
                st.session_state["messages"] = []
                st.session_state["show_chat_session"] = True
                st.session_state["agent_obj"] = None
                if st.session_state["use_backend_data"] == True:
                    st.session_state["agent_obj"] = AgentLift(
                        df_HY=pd.DataFrame(
                            st.session_state["backend_historical_expenses_data"]
                        ),
                        df_CY=pd.DataFrame(
                            st.session_state["backend_current_year_expenses_data"]
                        ),
                        df_Budget=pd.DataFrame(st.session_state["backend_budget_data"]),
                        file_path=f"src",
                        model_name=st.session_state["model_name"],
                    )
                else:
                    if (
                        st.session_state["historical_expenses_data_file_name"]
                        and st.session_state["current_year_expenses_data_file_name"]
                        and st.session_state["budget_data_file_name"]
                    ):
                        st.session_state["agent_obj"] = AgentLift(
                            df_HY=pd.DataFrame(
                                st.session_state["historical_expenses_data"]
                            ),
                            df_CY=pd.DataFrame(
                                st.session_state["current_year_expenses_data"]
                            ),
                            df_Budget=pd.DataFrame(st.session_state["budget_data"]),
                            file_path=f"src",
                            model_name=st.session_state["model_name"],
                        )
        with c4:
            chat_text = messages_to_text(st.session_state["messages"])
            st.download_button(
                label="⬇️",
                data=chat_text,
                file_name="chat_session.txt",
                mime="text/plain",
            )
    if st.session_state["agent_obj"]:
        # Chat session container
        if st.session_state["show_chat_session"]:
            with stylable_container(
                key="chat_session",
                css_styles=chat_container_css_styles,
            ):
                # Chat container
                chat_container = st.container()
                with chat_container:
                    for message in st.session_state["messages"]:
                        if message["role"] == "user":
                            with st.chat_message("user2", avatar=chat_avatars["User"]):
                                st.markdown(
                                    f"""
                                    <div style="
                                        background-color: {chat_avatars_color_bg['User']};
                                        color: {'black'};
                                        border-radius: 0.5em;
                                        padding: 1em;
                                        font-size: 16px;
                                    ">
                                        {message["content"]}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                        elif message["role"] == "assistant":
                            if message["error_response"] == True:
                                with st.chat_message(
                                    "assistant",
                                    avatar=chat_avatars["Error"],
                                ):
                                    st.markdown(
                                        f"""
                                            <div style="
                                                background-color: {chat_avatars_color_bg["Error"]};
                                                color: {'black'};
                                                border-radius: 0.5em;
                                                padding: 1em;
                                                font-size: 16px;
                                            ">
                                                {message["content"]}
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                            else:
                                with st.chat_message(
                                    "assistant",
                                    avatar=chat_avatars.get(
                                        message["agent"], "Assistant"
                                    ),
                                ):
                                    # Show the figure
                                    if message["figure_path"]:
                                        st.markdown(
                                            f"""
                                            <div style="
                                                background-color: {chat_avatars_color_bg.get(message['agent'], 'Assistant')};
                                                color: {'black'};
                                                border-radius: 0.5em 0.5em 0em 0em;
                                                padding: 1em;
                                                font-size: 16px;
                                            ">
                                            {message["content"]}
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                                        display_saved_plot(
                                            message["figure_path"],
                                            bg_color=chat_avatars_color_bg.get(
                                                message["agent"], "Assistant"
                                            ),
                                        )
                                    else:
                                        st.markdown(
                                            f"""
                                            <div style="
                                                background-color: {chat_avatars_color_bg.get(message['agent'], 'Assistant')};
                                                color: {'black'};
                                                border-radius: 0.5em;
                                                padding: 1em;
                                                font-size: 16px;
                                            ">
                                                {message["content"]}
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                    st.markdown("")

            chat_query_container_css_styles = """
                {
                    background-color: #FFFFFF;
                    padding-top: 1em;
                    padding-right: 1em;
                    padding-bottom: 2em;
                    padding-left: 1em;
                    border-radius: 0.5em;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                }
            """
            with stylable_container(
                key="chat_query_session",
                css_styles=chat_query_container_css_styles,
            ):
                # --- Chat input ---
                if prompt := st.chat_input(
                    "I'm your assistant. Ask me whenever you're ready!"
                ):

                    # 1️⃣ Show user message immediately
                    st.session_state.messages.append(
                        {
                            "role": "user",
                            "agent": "User",
                            "content": prompt,
                            "messages": [HumanMessage(content=prompt)],
                            "figure_path": None,
                            "next": "supervisor",
                            "call_bot": True,
                            "error_response": False,
                        }
                    )
                    st.rerun()  # Refresh UI so user message appears instantly

            # 2️⃣ After rerun, detect if last message is user and reply is missing
            # Previous query must be user query
            if (
                st.session_state.messages
                and st.session_state.messages[-1]["call_bot"] == True
                and st.session_state.messages[-1]["error_response"] == False
            ):
                previous_message_dict = st.session_state.messages[-1]

                # Get response from Bot
                with chat_container:
                    with st.chat_message(
                        "assistant",
                        avatar=chat_avatars.get(
                            previous_message_dict["next"], "Assistant"
                        ),
                    ):
                        with st.spinner("Generating..."):
                            try:
                                current_state = (
                                    st.session_state["agent_obj"]
                                    .graph.nodes[previous_message_dict["next"]]
                                    .invoke(
                                        {
                                            "messages": previous_message_dict[
                                                "messages"
                                            ],
                                            "next": previous_message_dict["next"],
                                        }
                                    )
                                )
                            except Exception as e:
                                # Add the message
                                st.session_state.messages.append(
                                    {
                                        "role": "assistant",
                                        "agent": previous_message_dict[
                                            "next"
                                        ],  # Agent answering the query
                                        "content": f"Error in bot response. Restart the chat session.\nError traceback: {e}",
                                        "messages": None,
                                        "figure_path": None,
                                        "next": None,
                                        "call_bot": False,
                                        "error_response": True,
                                    }
                                )
                                st.rerun()
                # Check if last previous messages are from bot (Not more than 10 responses must be from bot)
                reversed_messages = st.session_state.messages[::-1]
                # Base case
                current = reversed_messages[0]
                i = 1
                counter = 0
                while i < len(reversed_messages):
                    if current == reversed_messages[i]:
                        counter += 1
                        i += 1
                    else:
                        break

                # Add the message
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "agent": current_state["messages"][
                            0
                        ].name,  # Agent answering the query
                        "content": current_state["messages"][0].content,
                        "messages": add_messages(
                            previous_message_dict["messages"], current_state["messages"]
                        ),
                        "figure_path": current_state["messages"][
                            0
                        ].additional_kwargs.get("figure_path", None),
                        "next": current_state["next"],
                        "call_bot": (
                            True
                            if (current_state["next"] != "FINISH" and counter < 10)
                            else False
                        ),
                        "error_response": False,
                    }
                )
                st.rerun()
    else:
        warning_box("Agent not available!")

import streamlit as st
import pandas as pd
import base64
import copy
from io import BytesIO
from streamlit_extras.stylable_container import stylable_container
from PIL import Image
from components.file_manager import file_manager_component
from .ui_helpers import container_css_styles, get_default_network_tables
from .session_state_manager import init_session_state

# --- Style variables ---
text_color = "#E30A13"

def render_network_design():
    # --- Set Page Layout and Header ---
    with stylable_container(key="network_design_page", css_styles=container_css_styles):
        c1, _, c2 = st.columns([0.7, 0.1, 0.2], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<h2 style="color: {text_color}; margin: 0;">Supply Chain Network Simulator</h2>',
                unsafe_allow_html=True,
            )
    container_css_tabs_styles = """
    {
        background-color: #FFFFFF;
        padding-top: 1em;
        padding-right: 1em;
        padding-bottom: 1em;
        padding-left: 1em;
        border-radius: 1em;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        height: auto !important;
    }
    """
    with stylable_container(key="network_design_tabs", css_styles=container_css_tabs_styles):

        # --- Init Session State ---
        tabs = [
            "Factory Level",
            "Factory Product Level",
            "Warehouse Level",
            "Warehouse Factory Level",
            "Warehouse Product Level",
        ]
        init_session_state()

        # --- Upload/Delete/Download Section ---
        with st.container():
            _, col1, col2, col3 = st.columns([0.8, 0.075, 0.075, 0.075])

            with col1:
                action = file_manager_component()
                st.session_state.action = action

            # --- Handle Upload ---
            action = st.session_state.get("action")
            if (
                action
                and isinstance(action, dict)
                and "type" in action
                and "content" in action
                and action["type"] == "upload"
            ):
                try:
                    file_bytes = base64.b64decode(action["content"])
                    excel_file = BytesIO(file_bytes)
                    excel = pd.ExcelFile(excel_file)

                    uploaded_sheets = {}
                    for sheet in excel.sheet_names:
                        df = excel.parse(sheet)
                        uploaded_sheets[sheet] = df

                    if uploaded_sheets:
                        for key in list(st.session_state.keys()):
                            if key.startswith("editor_buffer_") or key.endswith("_table"):
                                del st.session_state[key]
                        for key in ["file_uploaded_once", "uploaded_sheets", "active_tab"]:
                            if key in st.session_state:
                                del st.session_state[key]

                        st.session_state.tables = uploaded_sheets
                        st.session_state.file_uploaded_once = True
                        st.session_state.uploaded_sheets = list(uploaded_sheets.keys())
                        st.session_state.active_tab = next(iter(uploaded_sheets))
                    else:
                        st.warning("⚠️ Uploaded file had no sheets or failed to parse.")
                except Exception as e:
                    st.error("❌ Error reading Excel file. Please try again.")
                    st.exception(e)

            # --- Download Button ---
            with col2:
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    for sheet, df in st.session_state.tables.items():
                        df.to_excel(writer, sheet_name=sheet[:31], index=False)

                st.download_button(
                    label="",
                    data=output.getvalue(),
                    file_name="network_new_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download all edited data",
                    icon=":material/download:"
                )

            with col3:
                if st.button("", 
                             help="Clear all uploaded data",
                             icon=":material/delete:"):
                    init_session_state()

        # --- Tab-wise Table Editors ---
        tab_objects = st.tabs(tabs)
        for tab_obj, tab_name in zip(tab_objects, tabs):
            with tab_obj:
                buffer_key = f"editor_buffer_{tab_name.replace(' ', '_')}"
                df_key = buffer_key.replace("editor_buffer_", "").lower() + "_table"

                # --- Per-tab Upload/Delete/Download ---
                with st.container():
                    _, c1, c2, c3 = st.columns([0.8, 0.075, 0.075, 0.075])
                    
                    # Upload per tab
                    with c1:
                        per_table_action = file_manager_component(key=f"file_manager_{df_key}")
                        if (
                            per_table_action
                            and isinstance(per_table_action, dict)
                            and "type" in per_table_action
                            and "content" in per_table_action
                            and per_table_action["type"] == "upload"
                        ):
                            try:
                                file_bytes = base64.b64decode(per_table_action["content"])
                                excel_file = BytesIO(file_bytes)
                                df = pd.read_excel(excel_file)
                                st.session_state.tables[tab_name] = df
                                st.session_state[buffer_key] = df.copy()
                                st.success(f"✅ {tab_name} uploaded successfully.")
                            except Exception as e:
                                st.error(f"❌ Failed to upload {tab_name}")
                                st.exception(e)

                    # Download per tab
                    with c2:
                        if buffer_key not in st.session_state:
                            st.session_state[buffer_key] = st.session_state.tables.get(tab_name, pd.DataFrame()).copy()
                        output = BytesIO()
                        st.session_state[buffer_key].to_excel(output, index=False)
                        st.download_button(
                            label="",
                            data=output.getvalue(),
                            file_name=f"{tab_name.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_btn_{df_key}",
                            icon=":material/download:"
                        )

                    # Delete per tab
                    with c3:
                        if st.button("", 
                                     key=f"delete_{df_key}",
                                     icon=":material/delete:"):
                            st.session_state.tables[tab_name] = pd.DataFrame()
                            st.session_state[buffer_key] = pd.DataFrame()
                            st.success(f"🗑️ {tab_name} data cleared.")

                # --- Render Table ---
                if tab_name not in st.session_state.tables or st.session_state.tables[tab_name].empty:
                    st.info("📂 No data available for this tab.")
                else:
                    if buffer_key not in st.session_state:
                        st.session_state[buffer_key] = st.session_state.tables[tab_name].copy()

                    df = st.session_state[buffer_key]
                    column_config = {}
                    for col in df.columns:
                        dtype = df[col].dtype
                        if pd.api.types.is_integer_dtype(dtype):
                            column_config[col] = st.column_config.NumberColumn(label=col, format="%d", step=1)
                        elif pd.api.types.is_float_dtype(dtype):
                            column_config[col] = st.column_config.NumberColumn(label=col, format="%.2f")
                        elif pd.api.types.is_bool_dtype(dtype):
                            column_config[col] = st.column_config.CheckboxColumn(label=col)
                        else:
                            column_config[col] = st.column_config.TextColumn(label=col)

                    edited_df = st.data_editor(
                        df.copy(),
                        num_rows="dynamic",
                        column_config=column_config,
                        hide_index=True,
                        use_container_width=True,
                        key=df_key
                    )

                    st.session_state[buffer_key] = edited_df.copy()
                    st.session_state.tables[tab_name] = edited_df.copy()
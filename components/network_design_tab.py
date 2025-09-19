import streamlit as st
import pandas as pd
import base64
import hashlib
from io import BytesIO
from streamlit_extras.stylable_container import stylable_container
from PIL import Image
from components.file_manager import file_manager_component
from .ui_helpers import container_css_styles
from .session_state_manager import init_session_state, reset_session_state
from components.ui_helpers import get_default_network_tables

# ---------- Helpers ----------
def _is_upload(d):
    return isinstance(d, dict) and d.get("type") == "upload" and "content" in d

def _md5_from_b64(b64_str: str) -> str:
    return hashlib.md5(base64.b64decode(b64_str)).hexdigest()

def _editor_key_for(tab_name: str) -> str:
    return f"editor_{tab_name.replace(' ', '_')}"

def _sync_latest(tab_name: str):
    """Force pull the latest editor buffer into tables right before use."""
    df_key = _editor_key_for(tab_name)
    buf_df = st.session_state.get(df_key)
    if isinstance(buf_df, pd.DataFrame):
        st.session_state.tables[tab_name] = buf_df.copy()

def _build_single_sheet(tab: str) -> bytes:
    _sync_latest(tab)  # ✅ flush before download
    buf = BytesIO()
    st.session_state.tables.get(tab, pd.DataFrame()).to_excel(buf, index=False)
    buf.seek(0)
    return buf.getvalue()

def _build_all_sheets(tabs_in_order: list[str]) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for sheet in tabs_in_order:
            _sync_latest(sheet)  # ✅ flush each before writing
            df = st.session_state.tables.get(sheet, pd.DataFrame())
            df.to_excel(writer, sheet_name=sheet[:31], index=False)
    buf.seek(0)
    return buf.getvalue()

# --- Style variables ---
text_color = "#E30A13"

def render_network_design():
    # --- Header ---
    with stylable_container(key="network_design_page", css_styles=container_css_styles):
        c1, _, c2 = st.columns([0.7, 0.1, 0.2], vertical_alignment="center")
        with c1:
            st.markdown(
                f'<h3 style="color: {text_color}; margin: 0;">Supply Chain Network Simulator</h3>',
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
        min-height: 518px;
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

        if "tables" not in st.session_state:
            init_session_state()
            print("✅ Session state initialized.")

        for tab in tabs:
            if tab not in st.session_state.tables:
                st.session_state.tables[tab] = pd.DataFrame()

        # --- Top bar: Upload / Download All / Clear ---
        with st.container():
            _, col1, col2, col3 = st.columns([0.8, 0.05, 0.05, 0.05])

            # Main upload (MD5 de-dup)
            with col1:
                action = file_manager_component(key="main_file_manager")
                st.session_state.action = action

            action = st.session_state.get("action")
            if _is_upload(action):
                try:
                    fp = _md5_from_b64(action["content"])
                    if st.session_state.get("_main_upload_md5") != fp:
                        file_bytes = base64.b64decode(action["content"])
                        excel_file = BytesIO(file_bytes)
                        excel = pd.ExcelFile(excel_file)
                        uploaded_sheets = {s: excel.parse(s) for s in excel.sheet_names}
                        if uploaded_sheets:
                            for sheet_name, df in uploaded_sheets.items():
                                if sheet_name in tabs:
                                    st.session_state.tables[sheet_name] = df.copy()
                            st.session_state["_main_upload_md5"] = fp
                            st.session_state.file_uploaded_once = True
                            st.session_state.uploaded_sheets = list(uploaded_sheets.keys())
                            st.session_state.active_tab = next(iter(uploaded_sheets))
                            print("📥 Main file uploaded once with sheets:", st.session_state.uploaded_sheets)
                        else:
                            st.warning("⚠️ Uploaded file had no sheets or failed to parse.")
                except Exception as e:
                    st.error("❌ Error reading Excel file. Please try again.")
                    st.exception(e)
                    print("❌ Error while processing main upload:", str(e))
                finally:
                    st.session_state["action"] = None

            # Download All (flush all editors before writing)
            with col2:
                clicked = st.download_button(
                    label="",
                    data=_build_all_sheets(tabs),
                    file_name="network_new_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download all edited data",
                    icon=":material/download:"
                )
                if clicked:
                    print("📤 Downloading all sheet data as Excel.")

            with col3:
                if st.button("", help="Clear all uploaded data", icon=":material/delete:"):
                    reset_session_state()
                    # Also clear editor buffers
                    for t in tabs:
                        k = _editor_key_for(t)
                        if k in st.session_state:
                            del st.session_state[k]
                    st.toast("🗑️ All data cleared")
                    print("🗑️ All data cleared via reset button.")

        # --- Center tabs using CSS ---
        st.markdown(
            """
            <style>
            .stTabs [data-baseweb="tab-list"] {
                justify-content: center;
                padding: 0.5em 0;
                border-radius: 1em;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # --- Tabs ---
        tab_objects = st.tabs(tabs)
        for tab_obj, tab_name in zip(tab_objects, tabs):
            with tab_obj:
                df_key = _editor_key_for(tab_name)

                # Per-tab toolbar
                with st.container():
                    _, c1, c2, c3 = st.columns([0.8, 0.05, 0.05, 0.06])

                    # Per-tab upload (MD5 de-dup)
                    with c1:
                        per_table_action = file_manager_component(key=f"file_manager_{df_key}")
                        if _is_upload(per_table_action):
                            try:
                                fp = _md5_from_b64(per_table_action["content"])
                                guard_key = f"__md5_{df_key}"
                                if st.session_state.get(guard_key) != fp:
                                    file_bytes = base64.b64decode(per_table_action["content"])
                                    excel_file = BytesIO(file_bytes)
                                    df_up = pd.read_excel(excel_file)
                                    st.session_state.tables[tab_name] = df_up.copy()
                                    st.session_state[guard_key] = fp
                                    st.success(f"✅ {tab_name} uploaded successfully.")
                                    print(f"📥 Uploaded data for tab: {tab_name}")
                            except Exception as e:
                                st.error(f"❌ Failed to upload {tab_name}")
                                st.exception(e)
                                print(f"❌ Error uploading file for tab: {tab_name} —", str(e))

                    # Per-tab download (flush latest before building)
                    with c2:
                        clicked_tab = st.download_button(
                            label="",
                            data=_build_single_sheet(tab_name),
                            file_name=f"{tab_name.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_btn_{df_key}",
                            icon=":material/download:"
                        )
                        if clicked_tab:
                            print(f"📤 Downloading data for tab: {tab_name}")

                    # Per-tab delete
                    with c3:
                        if st.button("", key=f"delete_{df_key}", icon=":material/delete:"):
                            defaults = get_default_network_tables()
                            st.session_state.tables[tab_name] = defaults.get(tab_name, pd.DataFrame())
                            if df_key in st.session_state:
                                del st.session_state[df_key]
                            st.success(f"🗑️ {tab_name} data cleared.")
                            print(f"🗑️ Cleared data for tab: {tab_name}")

                # Table editor
                container_css_table_styles = """
                { background-color: #FFFFFF; }
                """
                with stylable_container(key=f"design_tables_{tab_name.replace(' ', '_')}",
                                        css_styles=container_css_table_styles):
                    print(f"📝 Rendering data editor for tab: {tab_name}")

                    df = st.session_state.tables.get(tab_name, pd.DataFrame())
                    if df.empty:
                        st.info("📂 No data available for this tab.")
                    else:
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
                            df,
                            key=df_key,
                            column_config=column_config,
                            hide_index=True,
                            use_container_width=True,
                            num_rows="dynamic",
                        )
                        if isinstance(edited_df, pd.DataFrame):
                            st.session_state.tables[tab_name] = edited_df.copy()
                            st.session_state[f"last_commit_{tab_name}"] = pd.Timestamp.now()
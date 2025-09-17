import streamlit as st

def render_header(page_name: str):
    
    with st.container():
        col1, col2 = st.columns([8, 2])
        with col1:
            st.markdown("## Supply Chain Network Simulator")
        with col2:
            st.image("logo/sigmoid_logo.png", width=100)
        st.markdown("</div>", unsafe_allow_html=True)
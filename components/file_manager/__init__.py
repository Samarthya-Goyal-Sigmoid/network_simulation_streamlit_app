import os
import streamlit.components.v1 as components

# Absolute path to frontend/build
parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "frontend", "build")

# Declare the component
file_manager_component = components.declare_component(
    "file_manager", path=build_dir  # This uses the built frontend
)
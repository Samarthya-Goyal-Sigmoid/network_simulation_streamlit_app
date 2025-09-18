import os
import streamlit.components.v1 as components

# Step 1: Get absolute path
parent_dir = os.path.dirname(os.path.abspath(__file__))
print("🛠️ [DEBUG] Parent directory:", parent_dir)

# Step 2: Build directory path
build_dir = os.path.join(parent_dir, "frontend", "build")
print("📦 [DEBUG] Frontend build directory path:", build_dir)

# Step 3: Check if build folder exists
if not os.path.exists(build_dir):
    print("❌ [ERROR] Build folder not found at:", build_dir)
else:
    print("✅ [DEBUG] Build folder found. Declaring Streamlit component...")

# Step 4: Declare component
file_manager_component = components.declare_component(
    "file_manager", path=build_dir
)

print("🚀 [DEBUG] file_manager component declared successfully.")
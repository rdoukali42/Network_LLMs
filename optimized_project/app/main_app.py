"""
Main Streamlit application entry point for the Optimized AI Support Ticket System.
Handles routing between login and the main ticket interface.
"""

import streamlit as st
import sys
from pathlib import Path

# Determine the optimized_project root directory dynamically
# Assuming this file is in optimized_project/app/main_app.py
OPTIMIZED_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add optimized_project root to sys.path for imports like 'from config import app_config'
# and for AppWorkflowClient to find 'core'
if str(OPTIMIZED_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT))

# Imports from within the 'app' package (sibling modules)
from .auth import handle_authentication  # Using relative import
from .tickets_ui import show_ticket_interface # Will be created from front/tickets/__init__.py

# Imports from 'config' package (now at optimized_project/config/)
from config import app_config # app_config.py contains APP_TITLE etc.

# The AppWorkflowClient will initialize the AISystem from core.
# We might not need to import it directly here in main_app.py,
# but other UI modules will use it.
# from .workflow_client import AppWorkflowClient # For explicit init if needed by UI setup

def initialize_session_state():
    """Initializes required session state variables if they don't exist."""

    # Core authentication state
    if app_config.SESSION_KEYS["authenticated"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["authenticated"]] = False
    if app_config.SESSION_KEYS["username"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["username"]] = None # Initialize to None

    # Other session keys that were consolidated into app_config
    # Most of these will be initialized by their respective components when first accessed.
    # However, it's good practice to ensure some critical ones are present.
    if app_config.SESSION_KEYS["show_registration"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["show_registration"]] = False


def run_app():
    """Main application function to run the Streamlit app."""
    st.set_page_config(
        page_title=app_config.APP_TITLE,
        page_icon=app_config.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Perform environment check (e.g., for frontend-specific settings if any)
    # Note: Backend (AISystem) checks its own environment via CoreConfigLoader
    missing_frontend_vars = app_config.check_environment()
    if missing_frontend_vars:
        st.error(
            f"Missing required frontend environment variables: {', '.join(missing_frontend_vars)}. "
            "Please check your setup."
        )
        # Potentially stop the app here if these are critical for the UI
        # return

    initialize_session_state()

    # Authentication logic
    if not st.session_state.get(app_config.SESSION_KEYS["authenticated"], False):
        # print("main_app.py: User not authenticated, calling handle_authentication()")
        handle_authentication()
    else:
        # print(f"main_app.py: User authenticated as {st.session_state.get(app_config.SESSION_KEYS['username'])}, showing ticket interface.")
        # User is authenticated, show the main application interface
        show_ticket_interface()

if __name__ == "__main__":
    # This allows running the Streamlit app directly using `python optimized_project/app/main_app.py`
    # after navigating to the `optimized_project` root or ensuring PYTHONPATH is set.
    # For Streamlit, typical run is `streamlit run optimized_project/app/main_app.py` from project root.

    # print(f"Optimized Project Root (determined by main_app.py): {OPTIMIZED_PROJECT_ROOT}")
    # print(f"System Path: {sys.path}")
    run_app()

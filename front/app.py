"""
Main Streamlit application entry point.
Handles routing between login and chat interface.
"""

import streamlit as st
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent
front_dir = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(front_dir))

from auth import handle_authentication
from modern_ticket_interface import show_modern_ticket_interface
from streamlit_config import APP_TITLE, APP_ICON, SESSION_KEYS, check_environment
from service_integration import ServiceIntegration

def main():
    """Main application function."""
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide"
    )
    
    # Check environment
    missing_vars = check_environment()
    if missing_vars:
        st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        st.info("Please set up your .env file with the required API keys.")
        return
    
    # Initialize session state
    if SESSION_KEYS["authenticated"] not in st.session_state:
        st.session_state[SESSION_KEYS["authenticated"]] = False
    
    # Initialize service integration
    if "service_integration" not in st.session_state:
        st.session_state.service_integration = ServiceIntegration()
    
    # Handle authentication
    if not st.session_state[SESSION_KEYS["authenticated"]]:
        handle_authentication()
    else:
        show_modern_ticket_interface()

if __name__ == "__main__":
    main()

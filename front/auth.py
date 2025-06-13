"""
Authentication component for Streamlit app.
Handles user login functionality.
"""

import streamlit as st
import sys
from pathlib import Path

# Add front directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from streamlit_config import DEFAULT_USERS

def handle_authentication():
    """Handle user authentication."""
    st.title("🔐 Login to AI Chat System")
    
    with st.form("login_form"):
        st.markdown("### Please enter your credentials")
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

def authenticate_user(username: str, password: str) -> bool:
    """
    Simple authentication function.
    In production, this should connect to a proper authentication system.
    """
    return username in DEFAULT_USERS and DEFAULT_USERS[username] == password

def logout():
    """Handle user logout."""
    st.session_state.authenticated = False
    if "username" in st.session_state:
        del st.session_state.username
    if "chat_history" in st.session_state:
        del st.session_state.chat_history
    st.rerun()

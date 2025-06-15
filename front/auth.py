"""
Authentication component for Streamlit app.
Handles user login functionality with employee database integration.
"""

import streamlit as st
import sys
from pathlib import Path

# Add front directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from streamlit_config import DEFAULT_USERS
from database import db_manager

def handle_authentication():
    """Handle user authentication with registration option."""
    st.title("🔐 AI Support Ticket System")
    
    # Login/Register toggle
    if "show_registration" not in st.session_state:
        st.session_state.show_registration = False
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔐 Login", use_container_width=True, type="primary" if not st.session_state.show_registration else "secondary"):
            st.session_state.show_registration = False
            st.rerun()
    
    with col2:
        if st.button("👥 Register as Employee", use_container_width=True, type="primary" if st.session_state.show_registration else "secondary"):
            st.session_state.show_registration = True
            st.rerun()
    
    if st.session_state.show_registration:
        show_registration_interface()
    else:
        show_login_interface()

def show_login_interface():
    """Show the login form."""
    st.markdown("### Please enter your credentials")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Login", use_container_width=True)
        
        with col2:
            demo_login = st.form_submit_button("Demo Login (admin/admin)", use_container_width=True)
        
        if submitted:
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                
                # Get employee details if available
                employee = db_manager.get_employee_by_username(username)
                if employee:
                    st.session_state.employee_data = employee
                    st.session_state.user_full_name = employee['full_name']
                    st.session_state.user_role = employee['role_in_company']
                    # Set status to Available on login
                    db_manager.update_employee_status(username, 'Available')
                else:
                    st.session_state.employee_data = None
                    st.session_state.user_full_name = username
                    st.session_state.user_role = "System User"
                
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
        
        if demo_login:
            # Demo login
            st.session_state.authenticated = True
            st.session_state.username = "admin"
            st.session_state.employee_data = None
            st.session_state.user_full_name = "Administrator"
            st.session_state.user_role = "System Admin"
            st.success("Demo login successful! Redirecting...")
            st.rerun()

def show_registration_interface():
    """Show the registration interface."""
    from registration import show_registration_form
    show_registration_form()

def authenticate_user(username: str, password: str) -> bool:
    """
    Enhanced authentication function that checks both default users and employee database.
    """
    # Check default users first (admin accounts)
    if username in DEFAULT_USERS and DEFAULT_USERS[username] == password:
        return True
    
    # Check employee database
    employee = db_manager.get_employee_by_username(username)
    if employee:
        # For now, we don't store passwords for employees
        # In a real system, you'd verify against stored password hashes
        # For demo purposes, we'll accept any employee with a simple password
        if password == "employee123" or password == username:  # Simple demo password
            return True
    
    return False

def logout():
    """Handle user logout."""
    # Set user status to Offline before clearing session
    if 'username' in st.session_state:
        employee = db_manager.get_employee_by_username(st.session_state.username)
        if employee:
            db_manager.update_employee_status(st.session_state.username, 'Offline')
    
    # Clear all session state
    keys_to_clear = [
        "authenticated", "username", "employee_data", 
        "user_full_name", "user_role", "ticket_manager", 
        "workflow_client", "show_registration"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    # Legacy cleanup
    if "chat_history" in st.session_state:
        del st.session_state.chat_history
    st.rerun()

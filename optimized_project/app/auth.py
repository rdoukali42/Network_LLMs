"""
Authentication component for the Optimized Streamlit app.
Handles user login and registration toggling.
"""

import streamlit as st
from pathlib import Path

# Assuming this file is in optimized_project/app/
# For imports like data_management and config
OPTIMIZED_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT))
    st.session_state.sys_path_optimized_project = sys.path[:] # Store it to avoid re-adding if module reloads

from config import app_config # From optimized_project/config/app_config.py
from data_management.database import DatabaseManager # From optimized_project/data_management/database.py

# Registration UI will be in its own module
from .registration_ui import show_registration_form

# Initialize DatabaseManager instance - this should ideally be a singleton managed by the app
# For now, instantiate it here. A better approach might be to pass it around or use a global context.
# AISystem also instantiates it. For UI interactions not going via AISystem, UI needs access.
# This could be managed via a central app context or passed down from main_app.py if needed.
# For simplicity in this refactor, direct instantiation where needed by UI, but be mindful of multiple instances.
db_manager_instance = DatabaseManager(project_root_path=OPTIMIZED_PROJECT_ROOT)


def handle_authentication():
    """Handles the display of login or registration UI components."""
    st.title(f"{app_config.APP_ICON} AI Support Ticket System")

    # Use session keys from app_config
    show_reg_key = app_config.SESSION_KEYS["show_registration"]

    # Ensure show_registration key is initialized (already done in main_app.initialize_session_state)
    # if show_reg_key not in st.session_state:
    #     st.session_state[show_reg_key] = False

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🔐 Login", use_container_width=True,
                      type="primary" if not st.session_state[show_reg_key] else "secondary"):
            st.session_state[show_reg_key] = False
            st.rerun() # Rerun to reflect UI change immediately
    with col2:
        if st.button("👥 Register as Employee", use_container_width=True,
                      type="primary" if st.session_state[show_reg_key] else "secondary"):
            st.session_state[show_reg_key] = True
            st.rerun() # Rerun to reflect UI change

    if st.session_state[show_reg_key]:
        show_registration_form(db_manager=db_manager_instance) # Pass db_manager
    else:
        show_login_interface()


def show_login_interface():
    """Displays the login form and handles login logic."""
    st.markdown("### Please enter your credentials")

    with st.form("login_form_optimized"):
        username = st.text_input("Username", placeholder="Enter your username", key="login_username_opt")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password_opt")

        submit_col, demo_col = st.columns(2)
        with submit_col:
            login_submitted = st.form_submit_button("Login", use_container_width=True)
        with demo_col:
            demo_login_submitted = st.form_submit_button("Demo Login (admin/admin)", use_container_width=True)

        if login_submitted:
            if _authenticate_user_credentials(username, password):
                # Set session state variables using app_config keys
                st.session_state[app_config.SESSION_KEYS["authenticated"]] = True
                st.session_state[app_config.SESSION_KEYS["username"]] = username

                employee_details = db_manager_instance.get_employee_by_username(username)
                if employee_details:
                    st.session_state[app_config.SESSION_KEYS["employee_data"]] = employee_details
                    st.session_state[app_config.SESSION_KEYS["user_full_name"]] = employee_details.get('full_name', username)
                    st.session_state[app_config.SESSION_KEYS["user_role"]] = employee_details.get('role_in_company', "System User")
                    db_manager_instance.update_employee_status(username, 'Available') # Set status
                else:
                    # Handle non-employee users (e.g., admin from DEFAULT_USERS not in DB)
                    st.session_state[app_config.SESSION_KEYS["employee_data"]] = None
                    st.session_state[app_config.SESSION_KEYS["user_full_name"]] = username.capitalize()
                    st.session_state[app_config.SESSION_KEYS["user_role"]] = "System Admin" if username == "admin" else "User"

                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

        if demo_login_submitted:
            # Perform demo login (admin/admin)
            st.session_state[app_config.SESSION_KEYS["authenticated"]] = True
            st.session_state[app_config.SESSION_KEYS["username"]] = "admin"
            st.session_state[app_config.SESSION_KEYS["employee_data"]] = None # Demo admin might not be in DB
            st.session_state[app_config.SESSION_KEYS["user_full_name"]] = "Administrator (Demo)"
            st.session_state[app_config.SESSION_KEYS["user_role"]] = "System Admin"
            st.success("Demo login successful! Redirecting...")
            st.rerun()

def _authenticate_user_credentials(username: str, password: str) -> bool:
    """
    Authenticates user against default users and the employee database.
    (Helper function, prefixed with _ if not intended for direct import elsewhere)
    """
    # Check default users (from app_config)
    if username in app_config.DEFAULT_USERS and app_config.DEFAULT_USERS[username] == password:
        return True

    # Check employee database (using db_manager_instance)
    employee = db_manager_instance.get_employee_by_username(username)
    if employee:
        # Simplified password check for demo purposes (as in original)
        # In production, use hashed passwords and secure comparison.
        if password == "employee123" or password == username:
            return True

    return False

def logout_user():
    """Handles user logout: clears session and updates status."""
    username = st.session_state.get(app_config.SESSION_KEYS["username"])
    if username:
        employee = db_manager_instance.get_employee_by_username(username)
        if employee: # Only update status if they are an employee in the DB
            db_manager_instance.update_employee_status(username, 'Offline')

    # Clear all relevant session state keys defined in app_config.SESSION_KEYS
    # This is more robust than a hardcoded list if SESSION_KEYS evolves.
    for key_name in app_config.SESSION_KEYS.values():
        if key_name in st.session_state:
            del st.session_state[key_name]

    # Explicitly ensure core auth flag is reset
    st.session_state[app_config.SESSION_KEYS["authenticated"]] = False
    st.session_state[app_config.SESSION_KEYS["username"]] = None

    # print("User logged out, session cleared.")
    st.rerun()

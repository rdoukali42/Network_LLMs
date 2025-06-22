"""
Main ticket system UI for the Optimized Streamlit app.
Handles ticket creation, status tracking, and response management.
Orchestrates various UI components related to tickets.
"""

import streamlit as st
from pathlib import Path
from typing import Any # For type hinting

# Assuming this file is in optimized_project/app/
OPTIMIZED_PROJECT_ROOT_TICKETS_UI = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT_TICKETS_UI) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT_TICKETS_UI))

from config import app_config # For session keys and app title/icon
from data_management.ticket_store import TicketManager
from data_management.database import DatabaseManager # For employee checks and some UI elements
from .workflow_client import AppWorkflowClient # Bridge to AI system

# Import UI sub-modules (now in the same 'app' package)
from .smart_refresh_ui import (
    init_smart_refresh_session_state,
    check_for_ticket_updates_and_notify,
    render_smart_refresh_sidebar_controls,
    display_smart_refresh_notifications
)
from .availability_ui import render_availability_status_sidebar
from .call_ui import show_active_call_interface #, _get_voice_service_client # For checking if voice is enabled
from .ticket_forms_ui import show_create_ticket_form_ui, show_user_tickets_ui, show_assigned_tickets_ui
from .auth import logout_user # For logout button
from .registration_ui import show_employee_management # For admin panel

# One-time initialization of shared components, storing them in session state
def _initialize_ui_services():
    """Initializes and stores shared service instances in session state if not already present."""
    # Database Manager (used by multiple UI components)
    if "db_manager_instance_ui" not in st.session_state: # Using a distinct key for UI instance
        st.session_state.db_manager_instance_ui = DatabaseManager(project_root_path=OPTIMIZED_PROJECT_ROOT_TICKETS_UI)
        # print("tickets_ui: DatabaseManager initialized for UI.")

    # Ticket Manager
    if app_config.SESSION_KEYS["ticket_manager"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["ticket_manager"]] = TicketManager(project_root_path=OPTIMIZED_PROJECT_ROOT_TICKETS_UI)
        # print("tickets_ui: TicketManager initialized.")

    # AI Workflow Client
    if app_config.SESSION_KEYS["workflow_client"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["workflow_client"]] = AppWorkflowClient() # Singleton handles AISystem init
        # print("tickets_ui: AppWorkflowClient initialized.")

    # Voice Service Client (for checking if voice is enabled and for call_ui)
    if app_config.SESSION_KEYS["voice_service_client"] not in st.session_state:
        # This initialization is a bit heavy here. Ideally, this is configured once.
        # For now, using the same fallback logic as in call_ui.py's _get_voice_service_client
        try:
            from core.services import VoiceService
            from config.core_config import CoreConfigLoader
            cfg_loader = CoreConfigLoader(base_project_root=OPTIMIZED_PROJECT_ROOT_TICKETS_UI)
            core_cfg = cfg_loader.load_config_yaml() # Defaults to "development"
            voice_cfg = core_cfg.get("voice_service", {})
            # Determine the key for voice service's LLM model from core_config
            default_llm_model_key_for_voice = voice_cfg.get("chat_llm_model_key", "voice_service_llm_model")
            llm_cfg_for_voice = core_cfg.get("models", {}).get(default_llm_model_key_for_voice, {})
            # Ensure api_key_env_var is part of the llm_cfg_for_voice if not already
            llm_cfg_for_voice.setdefault("api_key_env_var", core_cfg.get("api_keys",{}).get("default_llm_api_key_env_var", "GEMINI_API_KEY"))

            st.session_state[app_config.SESSION_KEYS["voice_service_client"]] = VoiceService(
                voice_service_config=voice_cfg, llm_config=llm_cfg_for_voice
            )
            # print("tickets_ui: VoiceService client initialized.")
        except Exception as e:
            print(f"tickets_ui: Failed to initialize VoiceService client: {e}. Voice call features might be limited.")
            st.session_state[app_config.SESSION_KEYS["voice_service_client"]] = None

    # Smart Refresh session state init
    init_smart_refresh_session_state()

    # Call related session states (already in app_config.SESSION_KEYS, ensure they are initialized if not)
    # These are typically set by availability_ui or call_ui.
    if app_config.SESSION_KEYS["call_active"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["call_active"]] = False
    if app_config.SESSION_KEYS["call_info"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["call_info"]] = None
    if app_config.SESSION_KEYS["conversation_history"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["conversation_history"]] = []


def show_ticket_interface():
    """Displays the main ticket interface after user authentication."""

    _initialize_ui_services() # Ensure all shared services are ready

    # Retrieve instances from session state (or they are passed as args)
    db_manager = st.session_state.db_manager_instance_ui
    ticket_manager = st.session_state[app_config.SESSION_KEYS["ticket_manager"]]
    voice_service_client = st.session_state.get(app_config.SESSION_KEYS["voice_service_client"])


    # --- Sidebar ---
    with st.sidebar:
        st.image(str(OPTIMIZED_PROJECT_ROOT_TICKETS_UI / "app" / "static" / "logo_placeholder.png"), width=100) # Placeholder for a logo
        st.markdown(f"**User:** {st.session_state.get(app_config.SESSION_KEYS['user_full_name'], 'N/A')}")
        st.markdown(f"**Role:** {st.session_state.get(app_config.SESSION_KEYS['user_role'], 'N/A')}")
        st.divider()
        render_availability_status_sidebar(db_manager=db_manager, voice_service_client=voice_service_client)
        st.divider()
        render_smart_refresh_sidebar_controls()
        st.divider()
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            logout_user() # From auth.py
            st.rerun() # Ensure logout takes effect immediately

    # --- Main Page Content ---

    # Smart refresh check and notifications
    if st.session_state.get(app_config.SESSION_KEYS["smart_refresh_enabled"], False):
        if check_for_ticket_updates_and_notify(ticket_manager=ticket_manager):
            st.rerun() # Rerun to show new data if updates were detected
    display_smart_refresh_notifications() # Show notifications if any

    # Page Header
    st.title(f"{app_config.APP_ICON} Support Ticket System")

    # Admin: Employee Management Button
    # This check should be secure, e.g., based on role from DB or config, not just username "admin"
    current_username = st.session_state.get(app_config.SESSION_KEYS["username"])
    user_role = st.session_state.get(app_config.SESSION_KEYS["user_role"], "User")

    if user_role == "System Admin": # Or a more robust role check
        if st.button("👥 Manage Employees", key="admin_manage_employees_btn"):
            # Toggle a session state variable to show/hide employee management
            show_emp_manage_key = app_config.SESSION_KEYS["show_employee_management"]
            st.session_state[show_emp_manage_key] = not st.session_state.get(show_emp_manage_key, False)
            st.rerun() # Rerun to update view

    # Display Employee Management panel if toggled
    if st.session_state.get(app_config.SESSION_KEYS["show_employee_management"], False) and user_role == "System Admin":
        show_employee_management(db_manager=db_manager) # Pass db_manager
        return # Return early to only show employee management

    # Display Active Call Interface if a call is active
    if st.session_state.get(app_config.SESSION_KEYS["call_active"], False) and \
       st.session_state.get(app_config.SESSION_KEYS["call_info"]) is not None:
        # print("tickets_ui: Call is active, showing call interface.")
        show_active_call_interface() # This function will use VoiceService client from session or init it
        return # Return early to only show call interface

    # Main Ticket Tabs
    # Determine if user is an employee (can be assigned tickets)
    is_employee_in_db = False
    if current_username and db_manager:
        employee_record = db_manager.get_employee_by_username(current_username)
        if employee_record:
            is_employee_in_db = True

    if is_employee_in_db:
        tab_titles = ["📝 Create Ticket", "📋 My Tickets", "👨‍💼 Assigned to Me"]
        tab_create, tab_my_tickets, tab_assigned = st.tabs(tab_titles)
    else:
        tab_titles = ["📝 Create Ticket", "📋 My Tickets"]
        tab_create, tab_my_tickets = st.tabs(tab_titles)

    with tab_create:
        show_create_ticket_form_ui()
        # Instances of TicketManager, AppWorkflowClient, DatabaseManager are retrieved
        # from session state within show_create_ticket_form_ui or its called functions.
        # Alternatively, pass them: show_create_ticket_form_ui(ticket_manager, workflow_client, db_manager)

    with tab_my_tickets:
        show_user_tickets_ui() # Similarly, retrieves services from session or they are passed.

    if is_employee_in_db:
        with tab_assigned:
            show_assigned_tickets_ui() # Similarly

# Placeholder for logo if not found
def _ensure_static_assets():
    logo_path = OPTIMIZED_PROJECT_ROOT_TICKETS_UI / "app" / "static" / "logo_placeholder.png"
    if not logo_path.exists():
        logo_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Create a tiny transparent png if logo is missing to avoid errors
            from PIL import Image
            img = Image.new('RGBA', (1, 1), (0,0,0,0)) # Transparent
            img.save(logo_path, "PNG")
            print(f"Created placeholder logo at {logo_path}")
        except ImportError:
            print("PIL (Pillow) not installed, cannot create placeholder logo. Please ensure logo exists or install Pillow.")
        except Exception as e:
            print(f"Could not create placeholder logo: {e}")

if __name__ == '__main__':
    # This is for conceptual testing. `main_app.py` is the actual entry point.
    st.set_page_config(page_title="Tickets UI Test", layout="wide")
    _ensure_static_assets()

    # Mock session state for testing this module directly
    st.session_state[app_config.SESSION_KEYS["username"]] = "testuser" # or "admin" for admin view
    st.session_state[app_config.SESSION_KEYS["user_full_name"]] = "Test User"
    st.session_state[app_config.SESSION_KEYS["user_role"]] = "User" # or "System Admin"
    st.session_state[app_config.SESSION_KEYS["authenticated"]] = True

    show_ticket_interface()
else:
    # Ensure static assets like logo exist when imported as a module
    _ensure_static_assets()

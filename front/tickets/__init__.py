"""
Ticket system module for Streamlit app.
Handles ticket creation, status tracking, and response management.
"""

from .ticket_manager import TicketManager
from .smart_refresh import (
    init_smart_refresh,
    check_for_ticket_updates,
    smart_refresh_controls,
    show_refresh_notifications
)
from .availability import render_availability_status
from .call_interface import show_active_call_interface, generate_solution_from_call
from .ticket_forms import (
    show_create_ticket_form,
    show_user_tickets,
    show_assigned_tickets,
    format_datetime
)
from .ticket_processing import process_ticket_with_ai

def show_ticket_interface():
    """Display the main ticket interface."""
    import streamlit as st
    from auth import logout
    from database import db_manager
    from workflow_client import WorkflowClient
    
    # Initialize smart refresh system
    init_smart_refresh()
    
    # Render availability status in sidebar first
    render_availability_status()
    
    # Add smart refresh controls to sidebar
    smart_refresh_controls()
    
    # Check for updates if smart refresh is enabled
    if st.session_state.smart_refresh_enabled:
        updates_detected = check_for_ticket_updates()
        if updates_detected:
            # Trigger a rerun to show new data, but preserve user state
            st.rerun()
    
    # Show notifications about detected changes
    show_refresh_notifications()
    
    # Header with user info and controls
    col1, col2, col3 = st.columns([3, 0.7, 0.7])
    
    with col1:
        # Show enhanced user information
        user_display = st.session_state.get("user_full_name", st.session_state.username)
        user_role = st.session_state.get("user_role", "User")
        st.title(f"🎫 Support Ticket System")
        
        # Smart refresh status indicator
        if st.session_state.smart_refresh_enabled:
            st.markdown(f"**Welcome {user_display}** | *{user_role}* | 🔄 *Auto-refresh ON*")
        else:
            st.markdown(f"**Welcome {user_display}** | *{user_role}*")
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, help="Refresh to see latest tickets"):
            # Clear cache to force full refresh
            st.session_state.cached_ticket_state = {}
            st.rerun()
    
    with col3:
        if st.button("Logout", use_container_width=True):
            logout()
    
    # Show employee management for admin users
    if st.session_state.username == "admin":
        if st.button("👥 Manage Employees", use_container_width=True):
            st.session_state.show_employee_management = not st.session_state.get("show_employee_management", False)
            st.rerun()
    
    # Employee management interface
    if st.session_state.get("show_employee_management", False):
        from registration import show_employee_management
        show_employee_management()
        return
    
    # Initialize ticket manager
    if "ticket_manager" not in st.session_state:
        st.session_state.ticket_manager = TicketManager()

    # Initialize workflow client
    if "workflow_client" not in st.session_state:
        st.session_state.workflow_client = WorkflowClient()
    
    # Initialize voice call session states
    if "incoming_call" not in st.session_state:
        st.session_state.incoming_call = False
    if "call_active" not in st.session_state:
        st.session_state.call_active = False
    if "call_info" not in st.session_state:
        st.session_state.call_info = None
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "vocal_chat" not in st.session_state:
        st.session_state.vocal_chat = None
    
    # Show active call interface if call is in progress
    if st.session_state.call_active and st.session_state.call_info:
        show_active_call_interface()
        return
    
    # Create tabs for different views
    if st.session_state.username in [emp['username'] for emp in db_manager.get_all_employees()]:
        # Employee view - show assigned tickets tab
        tab1, tab2, tab3 = st.tabs(["📝 Create Ticket", "📋 My Tickets", "👨‍💼 Assigned to Me"])
    else:
        # Regular user view
        tab1, tab2 = st.tabs(["📝 Create Ticket", "📋 My Tickets"])
    
    with tab1:
        show_create_ticket_form()
    
    with tab2:
        show_user_tickets()
    
    # Employee assigned tickets tab
    if st.session_state.username in [emp['username'] for emp in db_manager.get_all_employees()]:
        with tab3:
            show_assigned_tickets()

"""
Ticket system module for Streamlit app.
This module has been refactored to use the new service layer architecture.
The main functionality now uses modern_ticket_interface.py with service integration.
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
    """
    Legacy ticket interface function for backward compatibility.
    Now delegates to the modern ticket interface.
    """
    import streamlit as st
    
    # Redirect to modern interface
    st.info("🔄 Upgrading to new interface...")
    
    # Import and show modern interface
    from modern_ticket_interface import show_modern_ticket_interface
    show_modern_ticket_interface()

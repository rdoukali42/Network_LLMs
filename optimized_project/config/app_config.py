"""
Configuration settings for the Streamlit frontend app.
"""

import os

# App configuration
APP_TITLE = "Optimized AI Support Ticket System"
APP_ICON = "🚀" # New icon for the new app

# Default credentials
DEFAULT_USERS = {
    "admin": "admin123",
    "user": "user123",
    "demo": "demo"
}

# Session state keys
SESSION_KEYS = {
    "authenticated": "authenticated",
    "username": "username",
    "employee_data": "employee_data", # Added from auth.py for clarity
    "user_full_name": "user_full_name", # Added from auth.py for clarity
    "user_role": "user_role", # Added from auth.py for clarity
    "ticket_manager": "ticket_manager",
    "workflow_client": "workflow_client", # Client for backend AI system
    "voice_service_client": "voice_service_client", # Client for voice STT/TTS
    "show_registration": "show_registration", # From auth.py
    "show_employee_management": "show_employee_management", # From tickets/__init__.py
    # For voice call state, previously in tickets/__init__.py
    "incoming_call": "incoming_call",
    "call_active": "call_active",
    "call_info": "call_info",
    "conversation_history": "conversation_history",
    "vocal_chat": "vocal_chat", # This was SmoothVocalChat instance, will be VoiceServiceClient now
    # Smart refresh states from tickets/smart_refresh.py
    "smart_refresh_enabled": "smart_refresh_enabled",
    "last_ticket_check": "last_ticket_check",
    "cached_ticket_state": "cached_ticket_state",
    "refresh_notifications": "refresh_notifications",
    # Form submission tracking from tickets/ticket_forms.py
    "_form_interaction_time": "_form_interaction_time",
    "_last_form_submission": "_last_form_submission",
    "registration_success": "registration_success", # From registration.py
    # Call ring state from tickets/availability.py
    # Dynamic keys like f"call_ring_{call['id']}" will be handled in code
}

def check_environment():
    """
    Check if required environment variables are set for the frontend.
    Currently, none are strictly required for the frontend itself to run,
    but backend will need its own.
    """
    required_vars = [] # e.g., ["STREAMLIT_SOME_SETTING"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    return missing_vars

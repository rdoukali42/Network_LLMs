"""
Configuration settings for the Streamlit app.
Handles app-specific settings and environment variables.
"""

import os
from pathlib import Path

# App configuration
APP_TITLE = "AI Support Ticket System"
APP_ICON = "🎫"

# Default credentials (replace with proper authentication in production)
DEFAULT_USERS = {
    "admin": "admin123",
    "user": "user123", 
    "demo": "demo"
}

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
CONFIG_PATH = PROJECT_ROOT / "configs"

# Session state keys
SESSION_KEYS = {
    "authenticated": "authenticated",
    "username": "username", 
    "ticket_manager": "ticket_manager",
    "workflow_client": "workflow_client"
}

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["GOOGLE_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars

"""
Smart refresh system for automatic ticket updates detection.
"""

import streamlit as st
import time
import uuid
from datetime import datetime
from typing import List


def init_smart_refresh():
    """Initialize smart refresh monitoring system."""
    if "smart_refresh_enabled" not in st.session_state:
        st.session_state.smart_refresh_enabled = True
    if "last_ticket_check" not in st.session_state:
        st.session_state.last_ticket_check = time.time()
    if "cached_ticket_state" not in st.session_state:
        st.session_state.cached_ticket_state = {}
    if "refresh_notifications" not in st.session_state:
        st.session_state.refresh_notifications = []


def get_ticket_state_signature():
    """Get a signature of current ticket state for change detection."""
    try:
        tickets = st.session_state.ticket_manager.load_tickets()
        username = st.session_state.username
        
        # Create signature for different ticket views
        user_tickets = [t for t in tickets if t["user"] == username]
        assigned_tickets = [t for t in tickets if t.get("assigned_to") == username]
        
        signature = {
            "total_count": len(tickets),
            "user_count": len(user_tickets),
            "assigned_count": len(assigned_tickets),
            "last_modified": max([t.get("updated_at", t.get("created_at", "")) for t in tickets] + [""]),
            "user_last_modified": max([t.get("updated_at", t.get("created_at", "")) for t in user_tickets] + [""]),
            "assigned_last_modified": max([t.get("updated_at", t.get("created_at", "")) for t in assigned_tickets] + [""]),
        }
        return signature
    except Exception:
        return {}


def check_for_ticket_updates():
    """Check for ticket updates without disrupting user experience."""
    current_time = time.time()
    
    # Only check every 30 seconds to avoid performance issues
    if current_time - st.session_state.last_ticket_check < 30:
        return False
    
    # Don't check during sensitive operations
    if should_skip_auto_refresh():
        return False
    
    st.session_state.last_ticket_check = current_time
    
    # Get current ticket state
    current_signature = get_ticket_state_signature()
    cached_signature = st.session_state.cached_ticket_state
    
    # Compare signatures to detect changes
    changes_detected = []
    
    if cached_signature:
        if current_signature.get("user_count", 0) != cached_signature.get("user_count", 0):
            changes_detected.append("user_tickets")
        
        if current_signature.get("assigned_count", 0) != cached_signature.get("assigned_count", 0):
            changes_detected.append("assigned_tickets")
        
        if current_signature.get("user_last_modified", "") != cached_signature.get("user_last_modified", ""):
            changes_detected.append("user_updates")
        
        if current_signature.get("assigned_last_modified", "") != cached_signature.get("assigned_last_modified", ""):
            changes_detected.append("assigned_updates")
    
    # Update cached state
    st.session_state.cached_ticket_state = current_signature
    
    if changes_detected:
        add_refresh_notification(changes_detected)
        return True
    
    return False


def should_skip_auto_refresh():
    """Determine if auto-refresh should be skipped to avoid disrupting user."""
    # Skip during active voice calls
    if st.session_state.get("call_active", False):
        return True
    
    # Skip if user recently submitted a form or clicked a button
    if hasattr(st.session_state, '_form_interaction_time'):
        if time.time() - st.session_state._form_interaction_time < 120:  # 2 minutes
            return True
    
    # Skip if user is likely typing (heuristic based on text widget keys)
    text_widget_keys = [key for key in st.session_state.keys() if key.startswith('solution_') or 'description' in key.lower()]
    if text_widget_keys:
        # If any text widgets have content, assume user might be typing
        for key in text_widget_keys:
            if hasattr(st.session_state, key) and st.session_state[key] and len(str(st.session_state[key]).strip()) > 0:
                # Set a conservative interaction time if not already set
                if not hasattr(st.session_state, '_form_interaction_time'):
                    st.session_state._form_interaction_time = time.time()
                return True
    
    return False


def add_refresh_notification(changes: List[str]):
    """Add notification about detected changes."""
    notification_text = "🔔 Updates detected: "
    
    if "user_tickets" in changes:
        notification_text += "New tickets in 'My Tickets' "
    if "assigned_tickets" in changes:
        notification_text += "New assignments in 'Assigned to Me' "
    if "user_updates" in changes:
        notification_text += "Updates to your tickets "
    if "assigned_updates" in changes:
        notification_text += "Updates to assigned tickets "
    
    # Add timestamp
    timestamp = datetime.now().strftime("%H:%M:%S")
    notification = {
        "text": notification_text.strip(),
        "timestamp": timestamp,
        "id": str(uuid.uuid4())[:8]
    }
    
    # Keep only last 3 notifications
    st.session_state.refresh_notifications.append(notification)
    if len(st.session_state.refresh_notifications) > 3:
        st.session_state.refresh_notifications.pop(0)


def show_refresh_notifications():
    """Display refresh notifications to the user."""
    if st.session_state.refresh_notifications:
        for notification in st.session_state.refresh_notifications[-1:]:  # Show only the latest
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"{notification['text']} (at {notification['timestamp']})")
            with col2:
                if st.button("✖️", key=f"close_{notification['id']}", help="Dismiss notification"):
                    st.session_state.refresh_notifications = [
                        n for n in st.session_state.refresh_notifications 
                        if n['id'] != notification['id']
                    ]
                    st.rerun()


def smart_refresh_controls():
    """Show smart refresh controls in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Smart Refresh")
    
    # Toggle for smart refresh
    enabled = st.sidebar.checkbox(
        "Auto-detect ticket updates",
        value=st.session_state.smart_refresh_enabled,
        help="Automatically detect new tickets and updates every 30 seconds"
    )
    st.session_state.smart_refresh_enabled = enabled
    
    if enabled:
        # Show last check time
        last_check = datetime.fromtimestamp(st.session_state.last_ticket_check)
        st.sidebar.caption(f"Last checked: {last_check.strftime('%H:%M:%S')}")
        
        # Show current state
        signature = st.session_state.cached_ticket_state
        if signature:
            st.sidebar.caption(f"Monitoring: {signature.get('user_count', 0)} your tickets, {signature.get('assigned_count', 0)} assigned")
    
    # Manual refresh all
    if st.sidebar.button("🔄 Force Refresh Now", use_container_width=True, help="Manually refresh all ticket data"):
        st.session_state.cached_ticket_state = {}  # Clear cache to force update
        st.rerun()

"""
Smart refresh system for automatic ticket updates detection in the Optimized Streamlit app.
"""

import streamlit as st
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional # For type hinting

# Assuming this file is in optimized_project/app/
OPTIMIZED_PROJECT_ROOT_SMART_REFRESH = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT_SMART_REFRESH) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT_SMART_REFRESH))

from config import app_config # For session keys
# TicketManager will be passed as an argument to functions needing it.
# from data_management.ticket_store import TicketManager

def init_smart_refresh_session_state():
    """Initializes session state variables required for smart refresh."""
    if app_config.SESSION_KEYS["smart_refresh_enabled"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["smart_refresh_enabled"]] = True # Default to enabled
    if app_config.SESSION_KEYS["last_ticket_check"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["last_ticket_check"]] = time.time()
    if app_config.SESSION_KEYS["cached_ticket_state"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["cached_ticket_state"]] = {}
    if app_config.SESSION_KEYS["refresh_notifications"] not in st.session_state:
        st.session_state[app_config.SESSION_KEYS["refresh_notifications"]] = []

def _get_current_ticket_state_signature(ticket_manager: Any) -> Dict[str, Any]:
    """
    Generates a signature of the current ticket states relevant to the logged-in user.
    Args:
        ticket_manager: An instance of TicketManager.
    Returns:
        A dictionary representing the signature of current ticket states.
    """
    try:
        all_tickets = ticket_manager.load_tickets()
        current_username = st.session_state.get(app_config.SESSION_KEYS["username"])
        if not current_username: return {} # Should not happen if user is logged in

        user_tickets = [t for t in all_tickets if t.get("user") == current_username]
        assigned_tickets = [t for t in all_tickets if t.get("assigned_to") == current_username]

        # More robust way to get last modified time, handling missing keys
        def get_last_update(ticket_list):
            if not ticket_list: return ""
            return max(t.get("updated_at", t.get("created_at", "")) for t in ticket_list)

        signature = {
            "user_ticket_count": len(user_tickets),
            "assigned_ticket_count": len(assigned_tickets),
            "user_tickets_last_updated": get_last_update(user_tickets),
            "assigned_tickets_last_updated": get_last_update(assigned_tickets),
            # Optionally, a global last update time for all tickets if relevant for some users
            # "all_tickets_last_updated": get_last_update(all_tickets),
        }
        return signature
    except Exception as e:
        # print(f"SmartRefresh: Error generating ticket state signature: {e}")
        return {} # Return empty on error to prevent crashes

def _should_skip_auto_refresh_check() -> bool:
    """Determines if auto-refresh check should be skipped to avoid disrupting user actions."""
    if st.session_state.get(app_config.SESSION_KEYS["call_active"], False):
        return True # Skip during active voice calls

    # Skip if user recently interacted with a form (e.g., submitting ticket, solution)
    form_interaction_time = st.session_state.get(app_config.SESSION_KEYS["_form_interaction_time"], 0)
    if time.time() - form_interaction_time < 120:  # 2-minute cooldown after form interaction
        return True

    # Heuristic: Skip if user might be typing in a text area
    # This is tricky. A simpler check is if any st.text_area/text_input has focus, but Streamlit doesn't expose this.
    # The original check for text_widget_keys was broad. Let's simplify or remove if too disruptive.
    # For now, relying on the _form_interaction_time is safer.

    return False

def _add_refresh_notification_message(changed_aspects: List[str]):
    """Adds a notification message about detected changes."""
    if not changed_aspects: return

    text_parts = []
    if "user_tickets" in changed_aspects: text_parts.append("updates to 'My Tickets'")
    if "assigned_tickets" in changed_aspects: text_parts.append("updates to 'Assigned to Me'")
    # More granular changes like "new_user_ticket", "user_ticket_updated" could be used.

    if not text_parts: return

    notification_text = f"🔔 Updates detected for: {', '.join(text_parts)}."
    timestamp_str = datetime.now().strftime("%H:%M:%S")

    new_notification = {
        "id": str(uuid.uuid4())[:8],
        "text": notification_text,
        "timestamp": timestamp_str
    }

    # Add to session state list, keeping only the last few (e.g., 3)
    notifications_list = st.session_state.get(app_config.SESSION_KEYS["refresh_notifications"], [])
    notifications_list.append(new_notification)
    st.session_state[app_config.SESSION_KEYS["refresh_notifications"]] = notifications_list[-3:]


def check_for_ticket_updates_and_notify(ticket_manager: Any) -> bool:
    """
    Checks for ticket updates compared to a cached state and notifies if changes occur.
    Args:
        ticket_manager: An instance of TicketManager.
    Returns:
        True if significant updates were detected (and a rerun might be useful), False otherwise.
    """
    if not st.session_state.get(app_config.SESSION_KEYS["smart_refresh_enabled"], False):
        return False # Smart refresh is disabled

    current_time = time.time()
    last_check_time = st.session_state.get(app_config.SESSION_KEYS["last_ticket_check"], 0)

    # Configurable check interval (e.g., 30 seconds)
    check_interval_seconds = st.session_state.get("smart_refresh_interval", 30)
    if current_time - last_check_time < check_interval_seconds:
        return False # Not time to check yet

    if _should_skip_auto_refresh_check():
        # print("SmartRefresh: Skipping check due to recent user activity or active call.")
        return False

    st.session_state[app_config.SESSION_KEYS["last_ticket_check"]] = current_time

    current_sig = _get_current_ticket_state_signature(ticket_manager)
    cached_sig = st.session_state.get(app_config.SESSION_KEYS["cached_ticket_state"], {})

    if not current_sig: # Error getting current signature
        return False

    detected_changes: List[str] = []
    if cached_sig: # Only compare if there's a previous state
        if current_sig.get("user_ticket_count") != cached_sig.get("user_ticket_count") or \
           current_sig.get("user_tickets_last_updated") != cached_sig.get("user_tickets_last_updated"):
            detected_changes.append("user_tickets")

        if current_sig.get("assigned_ticket_count") != cached_sig.get("assigned_ticket_count") or \
           current_sig.get("assigned_tickets_last_updated") != cached_sig.get("assigned_tickets_last_updated"):
            detected_changes.append("assigned_tickets")

    # Update cache regardless of changes to have the latest state for next check
    st.session_state[app_config.SESSION_KEYS["cached_ticket_state"]] = current_sig

    if detected_changes:
        _add_refresh_notification_message(detected_changes)
        return True # Signal that updates were found

    return False

def display_smart_refresh_notifications():
    """Displays stored refresh notifications to the user, typically at the top of the page."""
    notifications = st.session_state.get(app_config.SESSION_KEYS["refresh_notifications"], [])
    # Display only the latest one for non-intrusiveness, or allow multiple.
    # For this example, let's show up to 1, and they can be dismissed.

    if notifications:
        # Displaying the most recent notification
        latest_notification = notifications[-1]
        notif_key = f"notif_dismiss_{latest_notification['id']}"

        # Use columns for dismiss button
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.info(f"{latest_notification['text']} (at {latest_notification['timestamp']})")
        with col2:
            if st.button("✖️", key=notif_key, help="Dismiss this notification"):
                # Remove this specific notification by ID
                current_notifications = st.session_state.get(app_config.SESSION_KEYS["refresh_notifications"], [])
                st.session_state[app_config.SESSION_KEYS["refresh_notifications"]] = [
                    n for n in current_notifications if n['id'] != latest_notification['id']
                ]
                st.rerun()


def render_smart_refresh_sidebar_controls():
    """Renders controls for smart refresh in the Streamlit sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Smart Refresh")

    enabled_key = app_config.SESSION_KEYS["smart_refresh_enabled"]
    is_enabled = st.sidebar.checkbox(
        "Auto-detect ticket updates",
        value=st.session_state.get(enabled_key, True), # Default to True if not set
        help="Automatically check for new tickets and updates periodically."
    )
    st.session_state[enabled_key] = is_enabled

    if is_enabled:
        last_check_ts = st.session_state.get(app_config.SESSION_KEYS["last_ticket_check"], time.time())
        last_check_dt = datetime.fromtimestamp(last_check_ts)
        st.sidebar.caption(f"Last auto-check: {last_check_dt.strftime('%H:%M:%S')}")

        cached_sig_info = st.session_state.get(app_config.SESSION_KEYS["cached_ticket_state"], {})
        if cached_sig_info:
            st.sidebar.caption(
                f"Monitoring: {cached_sig_info.get('user_ticket_count', 0)} your tickets, "
                f"{cached_sig_info.get('assigned_ticket_count', 0)} assigned."
            )

    if st.sidebar.button("🔄 Force Refresh Ticket Data Now", use_container_width=True, key="force_refresh_tickets_btn"):
        # Clear cached state to force re-evaluation on next check or manual load
        st.session_state[app_config.SESSION_KEYS["cached_ticket_state"]] = {}
        # Also clear notifications as user is forcing a full refresh
        st.session_state[app_config.SESSION_KEYS["refresh_notifications"]] = []
        st.rerun() # Rerun to reload ticket views immediately

# Example usage (conceptual, would be called in tickets_ui.py)
# if __name__ == '__main__':
#     # Requires Streamlit context and a TicketManager instance
#     st.title("Smart Refresh Test")
#     # Mock TicketManager for testing UI components
#     class MockTicketManager:
#         def load_tickets(self): return [{"id": "1", "user": "test", "assigned_to": "test", "updated_at": datetime.now().isoformat()}]

#     mock_tm = MockTicketManager()
#     st.session_state[app_config.SESSION_KEYS["username"]] = "test" # Simulate logged-in user

#     init_smart_refresh_session_state() # Call once at app startup or main page load
#     render_smart_refresh_sidebar_controls()

#     if check_for_ticket_updates_and_notify(ticket_manager=mock_tm):
#         st.write("Updates were detected by check_for_ticket_updates_and_notify!")
#         # In a real app, tickets_ui would now re-query tickets if a rerun happens.
#         # For this test, we just show the message.

#     display_smart_refresh_notifications() # Display any pending notifications

#     st.write("Main content area. Smart refresh controls are in the sidebar.")
#     st.write("Current cached state:", st.session_state.get(app_config.SESSION_KEYS["cached_ticket_state"]))
#     st.write("Current notifications:", st.session_state.get(app_config.SESSION_KEYS["refresh_notifications"]))

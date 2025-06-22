"""
Employee availability status management for the sidebar in the Optimized Streamlit app.
Handles display of current status, changing status, and incoming call notifications.
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import base64 # For encoding audio for autoplay
from typing import Any, Optional

# Assuming this file is in optimized_project/app/
OPTIMIZED_PROJECT_ROOT_AVAIL_UI = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT_AVAIL_UI) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT_AVAIL_UI))

from config import app_config # From optimized_project/config/app_config.py
# DatabaseManager instance will be passed as an argument.
# VoiceService client might be needed if this UI directly interacts with it,
# but for now, it sets session state that call_ui.py will use.

def render_availability_status_sidebar(db_manager: Any, voice_service_client: Optional[Any] = None):
    """
    Renders the availability status interface in the Streamlit sidebar.
    Args:
        db_manager: An instance of DatabaseManager.
        voice_service_client: An instance of VoiceService (or a client for it).
                              Currently used to check if voice capabilities are configured for enabling call features.
                              The actual voice call interaction is handled by call_ui.py.
    """
    username = st.session_state.get(app_config.SESSION_KEYS["username"])
    if not username:
        # This UI component should not be rendered if user is not logged in.
        # tickets_ui.py (or its equivalent) should guard this.
        return

    # Auto-cleanup expired statuses and update last seen
    db_manager.auto_cleanup_expired_statuses()
    db_manager.update_last_seen(username)

    availability_info = db_manager.get_employee_availability(username)
    current_status = availability_info.get('availability_status', 'Offline') if availability_info else 'Offline'

    st.sidebar.markdown("### 🔄 Availability Status")
    status_colors = {'Available': '🟢', 'In Meeting': '🔴', 'Busy': '🟡', 'Do Not Disturb': '🔴', 'Offline': '⚫'}
    st.sidebar.markdown(f"**Current:** {status_colors.get(current_status, '⚫')} {current_status}")

    # Employee check for status change and call notifications
    employee = db_manager.get_employee_by_username(username)
    if not employee: # Not a registered employee in the database
        st.sidebar.info("Register as an employee via Admin Panel to manage detailed availability and receive calls.")
        return # Non-employees don't get the rest of the controls

    # --- Incoming Call Notifications ---
    # This section assumes voice_service_client is available to indicate voice features are on.
    # The actual call answering logic will set session state for call_ui.py to pick up.
    if voice_service_client is not None: # Check if voice service is configured/passed
        pending_calls = db_manager.get_pending_calls(username)
        if pending_calls:
            _display_incoming_call_notification(db_manager, pending_calls[0]) # Show most recent

    # --- Status Selection ---
    status_options = ['Available', 'In Meeting', 'Busy', 'Do Not Disturb', 'Offline'] # Added Offline here
    try:
        current_idx = status_options.index(current_status)
    except ValueError:
        current_idx = status_options.index('Offline') # Default to Offline if status is weird

    selected_status = st.sidebar.selectbox(
        "Change Status:", status_options, index=current_idx, key="availability_status_select"
    )

    until_time_iso: Optional[str] = None
    if selected_status == 'In Meeting': # Example of status with duration
        st.sidebar.markdown("**Return Time (for 'In Meeting'):**")
        time_col1, time_col2 = st.sidebar.columns(2)
        with time_col1:
            hours = st.selectbox("Hours", range(0, 9), index=1, key="meeting_hours") # Default 1 hr
        with time_col2:
            minutes = st.selectbox("Minutes", [0, 15, 30, 45], index=0, key="meeting_minutes")
        if hours > 0 or minutes > 0 : # Only set if duration is positive
             until_time_iso = (datetime.now() + timedelta(hours=hours, minutes=minutes)).isoformat()

    if st.sidebar.button("Update Status", type="primary", key="update_status_button"):
        success, message = db_manager.update_employee_status(username, selected_status, until_time_iso)
        if success:
            st.sidebar.success(message)
            st.rerun()
        else:
            st.sidebar.error(message)

def _display_incoming_call_notification(db_manager: Any, call_data: Dict[str, Any]):
    """Helper to display an incoming call notification in the sidebar."""
    call_info = call_data.get('call_info', {}) # call_info is the JSON blob from the DB
    call_db_id = call_data.get('id')

    # Ringtone logic
    call_ring_key = f"call_ring_{call_db_id}"
    if call_ring_key not in st.session_state:
        st.session_state[call_ring_key] = True # Mark that we've started ringing for this call

        # Attempt to play ringtone (ensure static file path is correct for new structure)
        # Path should be relative to where streamlit is run, or absolute.
        # Using Path(__file__).parent points to 'app', then 'static'
        ringtone_path = Path(__file__).parent / "static" / "old_phone.mp3"
        if ringtone_path.exists():
            try:
                with open(ringtone_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                # Autoplay with loop - user browser might block this without interaction.
                st.sidebar.markdown(
                    f'<audio id="ringtone_{call_db_id}" autoplay loop><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                print(f"Could not play ringtone: {e}")
        else:
            print(f"Ringtone file not found at {ringtone_path}")

    st.sidebar.markdown("---")
    st.sidebar.subheader("📞 Incoming Call")
    st.sidebar.info(
        f"**From:** {call_info.get('caller_name', 'Unknown User')}\n"
        f"**Ticket:** {call_data.get('ticket_subject', 'N/A')}\n"
        f"**Ticket ID:** {call_data.get('ticket_id', 'N/A')}"
    )

    answer_col, decline_col = st.sidebar.columns(2)
    with answer_col:
        if st.button("📞 Answer", type="primary", use_container_width=True, key=f"answer_call_{call_db_id}"):
            if call_ring_key in st.session_state: del st.session_state[call_ring_key]
            # Stop audio using JavaScript if possible, as st.rerun might not be fast enough
            st.sidebar.markdown(f"<script>document.getElementById('ringtone_{call_db_id}')?.pause();</script>", unsafe_allow_html=True)


            st.session_state[app_config.SESSION_KEYS["call_active"]] = True
            # call_info from DB (the JSON blob) is directly passed to session state.
            # This contains ticket_data, employee_data etc needed by VoiceService & call_ui
            st.session_state[app_config.SESSION_KEYS["call_info"]] = call_info
            st.session_state[app_config.SESSION_KEYS["conversation_history"]] = []

            # The 'vocal_chat' session key, which previously held SmoothVocalChat instance,
            # is no longer needed here if VoiceService is instantiated on demand in call_ui.py
            # or passed around. For now, we ensure it's reset if it existed.
            if app_config.SESSION_KEYS["vocal_chat"] in st.session_state:
                 del st.session_state[app_config.SESSION_KEYS["vocal_chat"]]


            db_manager.update_call_status(call_db_id, 'answered')
            st.rerun() # Rerun to switch to call interface

    with decline_col:
        if st.button("📴 Decline", use_container_width=True, key=f"decline_call_{call_db_id}"):
            if call_ring_key in st.session_state: del st.session_state[call_ring_key]
            st.sidebar.markdown(f"<script>document.getElementById('ringtone_{call_db_id}')?.pause();</script>", unsafe_allow_html=True)

            db_manager.update_call_status(call_db_id, 'declined')
            st.rerun() # Refresh sidebar

# Example of how this might be called in tickets_ui.py (main screen after login)
# if __name__ == '__main__':
#     # This requires streamlit context and db_manager to be set up
#     # Mocking for conceptual display
#     st.session_state[app_config.SESSION_KEYS["username"]] = "test_employee"
#     class MockDBManager:
#         def get_employee_availability(self, uname): return {"availability_status": "Available", "last_seen": datetime.now().isoformat()}
#         def auto_cleanup_expired_statuses(self): pass
#         def update_last_seen(self, uname): pass
#         def get_employee_by_username(self, uname): return {"username": uname, "full_name": "Test Employee"} if uname == "test_employee" else None
#         def get_pending_calls(self, uname): return [] # Or mock a call
#         def update_call_status(self, call_id, status): print(f"Call {call_id} status to {status}")
#         def update_employee_status(self, uname, status, until=None): print(f"{uname} status to {status}"); return True, "Status updated"

#     mock_db = MockDBManager()
#     # In a real app, voice_service_client would be an instance of VoiceService or its client
#     # For this UI component, we only need to know if voice is configured to show call section.
#     mock_voice_service = object() # Presence indicates voice features are on

#     render_availability_status_sidebar(db_manager=mock_db, voice_service_client=mock_voice_service)
#     st.sidebar.markdown("---")
#     st.write("Main app content would be here.")

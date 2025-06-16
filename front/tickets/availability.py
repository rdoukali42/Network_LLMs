"""
Employee availability status management for sidebar.
"""

import streamlit as st
from datetime import datetime, timedelta
from database import db_manager


def render_availability_status():
    """Render availability status interface in sidebar."""
    if 'username' not in st.session_state:
        return
    
    username = st.session_state.username
    
    # Auto-cleanup expired statuses
    db_manager.auto_cleanup_expired_statuses()
    
    # Update last seen
    db_manager.update_last_seen(username)
    
    # Get current status
    availability = db_manager.get_employee_availability(username)
    current_status = availability.get('availability_status', 'Offline') if availability else 'Offline'
    
    st.sidebar.markdown("### 🔄 Availability Status")
    
    # Status colors
    status_colors = {
        'Available': '🟢',
        'In Meeting': '🔴', 
        'Busy': '🟡',
        'Do Not Disturb': '🔴',
        'Offline': '⚫'
    }
    
    # Display current status
    st.sidebar.markdown(f"**Current:** {status_colors.get(current_status, '⚫')} {current_status}")
    
    # Check for pending calls from database (for ASSIGNED EMPLOYEES)
    employee = db_manager.get_employee_by_username(username)
    if employee:
        pending_calls = db_manager.get_pending_calls(username)
        
        if pending_calls:
            # Show the most recent pending call
            call = pending_calls[0]
            call_info = call['call_info']
            
            # Play ringtone when call notification first appears
            call_notification_key = f"call_ring_{call['id']}"
            if call_notification_key not in st.session_state:
                # Mark that we've started ringing for this call
                st.session_state[call_notification_key] = True
                
                # Play ringtone
                import base64
                from pathlib import Path
                ringtone_path = Path(__file__).parent.parent / "media" / "old_phone.mp3"
                if ringtone_path.exists():
                    try:
                        with open(ringtone_path, "rb") as audio_file:
                            audio_bytes = audio_file.read()
                        audio_base64 = base64.b64encode(audio_bytes).decode()
                        
                        st.sidebar.markdown(f"""
                        <audio autoplay loop>
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                        </audio>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        print(f"Could not play ringtone: {e}")
            
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📞 Incoming Call")
            st.sidebar.markdown(f"**From:** {call_info.get('caller_name', 'Unknown User')}")
            st.sidebar.markdown(f"**Ticket:** {call['ticket_subject']}")
            st.sidebar.markdown(f"**Ticket ID:** {call['ticket_id']}")
            
            # Answer call button
            if st.sidebar.button("📞 Answer Call", type="primary", use_container_width=True):
                # Stop ringing by removing the ring state
                if call_notification_key in st.session_state:
                    del st.session_state[call_notification_key]
                
                # Set up call in session state
                st.session_state.call_active = True
                st.session_state.call_info = call_info
                st.session_state.conversation_history = []
                
                # Mark call as answered in database
                db_manager.update_call_status(call['id'], 'answered')
                
                # Initialize vocal chat
                if 'vocal_chat' not in st.session_state:
                    from vocal_components import SmoothVocalChat
                    st.session_state.vocal_chat = SmoothVocalChat()
                
                st.rerun()
            
            # Reject call button
            if st.sidebar.button("📴 Decline", use_container_width=True):
                # Stop ringing by removing the ring state
                if call_notification_key in st.session_state:
                    del st.session_state[call_notification_key]
                
                # Mark call as declined in database
                db_manager.update_call_status(call['id'], 'declined')
                st.rerun()
    
    # Status selection (only for registered employees)
    if employee:
        status_options = ['Available', 'In Meeting', 'Busy', 'Do Not Disturb']
        selected_status = st.sidebar.selectbox(
            "Change Status:",
            status_options,
            index=status_options.index(current_status) if current_status in status_options else 0
        )
        
        # Return time for "In Meeting"
        until_time = None
        if selected_status == 'In Meeting':
            st.sidebar.markdown("**Return Time:**")
            col1, col2 = st.sidebar.columns(2)
            with col1:
                hours = st.selectbox("Hours", range(1, 9), index=0, key="hours")
            with col2:
                minutes = st.selectbox("Minutes", [0, 15, 30, 45], index=0, key="minutes")
            
            until_time = (datetime.now() + timedelta(hours=hours, minutes=minutes)).isoformat()
        
        # Update status button
        if st.sidebar.button("Update Status", type="primary"):
            success, message = db_manager.update_employee_status(username, selected_status, until_time)
            if success:
                st.sidebar.success(message)
                st.rerun()
            else:
                st.sidebar.error(message)
    else:
        st.sidebar.info("Register as employee to set availability status")

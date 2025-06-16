"""
Ticket system component for Streamlit app.
Handles ticket creation, status tracking, and response management.
"""

import streamlit as st
import sys
import json
import uuid
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add paths for imports
project_root = Path(__file__).parent.parent
front_dir = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(front_dir))

from auth import logout
from workflow_client import WorkflowClient
from database import db_manager

# Ticket storage file
TICKETS_FILE = Path(__file__).parent / "tickets.json"


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


def add_refresh_notification(changes):
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
            
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📞 Incoming Call")
            st.sidebar.markdown(f"**From:** {call_info.get('caller_name', 'Unknown User')}")
            st.sidebar.markdown(f"**Ticket:** {call['ticket_subject']}")
            st.sidebar.markdown(f"**Ticket ID:** {call['ticket_id']}")
            
            # Answer call button
            if st.sidebar.button("📞 Answer Call", type="primary", use_container_width=True):
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


class TicketManager:
    """Manages ticket operations."""
    
    def __init__(self):
        self.ensure_tickets_file()
    
    def ensure_tickets_file(self):
        """Ensure tickets file exists."""
        if not TICKETS_FILE.exists():
            with open(TICKETS_FILE, 'w') as f:
                json.dump([], f)
    
    def load_tickets(self) -> List[Dict]:
        """Load all tickets from storage."""
        try:
            with open(TICKETS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_tickets(self, tickets: List[Dict]):
        """Save tickets to storage."""
        with open(TICKETS_FILE, 'w') as f:
            json.dump(tickets, f, indent=2, default=str)
    
    def create_ticket(self, user: str, category: str, priority: str, subject: str, description: str) -> str:
        """Create a new ticket."""
        tickets = self.load_tickets()
        
        ticket_id = str(uuid.uuid4())[:8]
        ticket = {
            "id": ticket_id,
            "user": user,
            "category": category,
            "priority": priority,
            "subject": subject,
            "description": description,
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "response": None,
            "response_at": None,
            "assigned_to": None,
            "assignment_status": None,
            "assignment_date": None,
            "employee_solution": None,
            "completion_date": None
        }
        
        tickets.append(ticket)
        self.save_tickets(tickets)
        return ticket_id
    
    def get_user_tickets(self, user: str) -> List[Dict]:
        """Get all tickets for a specific user."""
        tickets = self.load_tickets()
        return [t for t in tickets if t["user"] == user]
    
    def get_ticket_by_id(self, ticket_id: str) -> Optional[Dict]:
        """Get a specific ticket by ID."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                return ticket
        return None
    
    def update_ticket_response(self, ticket_id: str, response: str):
        """Update ticket with AI response."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                ticket["response"] = response
                ticket["response_at"] = datetime.now().isoformat()
                ticket["status"] = "Responded"
                ticket["updated_at"] = datetime.now().isoformat()
                break
        self.save_tickets(tickets)
    
    def assign_ticket(self, ticket_id: str, employee_username: str):
        """Assign ticket to an employee."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                ticket["assigned_to"] = employee_username
                ticket["assignment_status"] = "assigned"
                ticket["assignment_date"] = datetime.now().isoformat()
                ticket["status"] = "Assigned"
                ticket["updated_at"] = datetime.now().isoformat()
                break
        self.save_tickets(tickets)
    
    def update_employee_solution(self, ticket_id: str, solution: str):
        """Update ticket with employee solution."""
        tickets = self.load_tickets()
        for ticket in tickets:
            if ticket["id"] == ticket_id:
                ticket["employee_solution"] = solution
                ticket["assignment_status"] = "completed"
                ticket["completion_date"] = datetime.now().isoformat()
                ticket["status"] = "Solved"
                ticket["updated_at"] = datetime.now().isoformat()
                break
        self.save_tickets(tickets)
    
    def get_assigned_tickets(self, employee_username: str) -> List[Dict]:
        """Get tickets assigned to an employee."""
        tickets = self.load_tickets()
        return [t for t in tickets if t.get("assigned_to") == employee_username]

def show_ticket_interface():
    """Display the main ticket interface."""
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

def show_create_ticket_form():
    """Display the ticket creation form."""
    st.markdown("### Create New Support Ticket")
    
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Category",
                ["Technical Issue", "Feature Request", "Bug Report", "General Question", "Account Issue"],
                help="Select the category that best describes your issue"
            )
        
        with col2:
            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High", "Critical"],
                index=1,
                help="Select the urgency level of your issue"
            )
        
        subject = st.text_input(
            "Subject",
            placeholder="Brief description of your issue",
            help="Provide a clear, concise subject line"
        )
        
        description = st.text_area(
            "Description",
            placeholder="Provide detailed information about your issue, including steps to reproduce if applicable...",
            height=200,
            help="Be as detailed as possible to help us assist you better"
        )
        
        submit_button = st.form_submit_button("Submit Ticket", use_container_width=True)
        
        if submit_button:
            # Mark form interaction time to prevent auto-refresh disruption
            st.session_state._form_interaction_time = time.time()
            
            if subject.strip() and description.strip():
                # Create the ticket
                ticket_id = st.session_state.ticket_manager.create_ticket(
                    user=st.session_state.username,
                    category=category,
                    priority=priority,
                    subject=subject.strip(),
                    description=description.strip()
                )
                
                st.success(f"✅ Ticket created successfully! Ticket ID: **{ticket_id}**")
                st.info("Your ticket has been submitted and will be processed by our AI system. Check the 'My Tickets' tab for updates.")
                
                # Process ticket with AI in background
                process_ticket_with_ai(ticket_id, subject, description)
                
            else:
                st.error("Please fill in both subject and description fields.")

def process_ticket_with_ai(ticket_id: str, subject: str, description: str):
    """Process ticket with AI workflow."""
    try:
        # Combine subject and description for AI processing
        query = f"Support Ticket: {subject}\n\nDetails: {description}"
        
        # Process with AI workflow
        with st.spinner(f"Processing ticket {ticket_id} with AI..."):
            result = st.session_state.workflow_client.process_message(query)
            
            # Extract AI response from different possible formats
            response = None
            if result:
                # Try different response formats
                if isinstance(result, dict):
                    response = (result.get("result") or       # Main format from AISystem
                              result.get("synthesis") or 
                              result.get("response") or 
                              result.get("answer") or
                              result.get("output"))
                elif isinstance(result, str):
                    response = result
                
            if response and response.strip():
                # Check if this is an HR referral that should become an assignment
                if "👤" in response and "(@" in response and "🏢 **Role**:" in response:
                    # Parse employee username from response
                    username_match = response.split("(@")[1].split(")")[0] if "(@" in response else None
                    
                    if username_match:
                        # Verify employee exists and assign ticket
                        employee = db_manager.get_employee_by_username(username_match)
                        if employee:
                            st.session_state.ticket_manager.assign_ticket(ticket_id, username_match)
                            
                            # Trigger voice call with Vocal Assistant
                            ticket_data = st.session_state.ticket_manager.get_ticket_by_id(ticket_id)
                            if ticket_data:
                                # Store call notification for the ASSIGNED EMPLOYEE
                                call_info = {
                                    "ticket_id": ticket_id,
                                    "employee_name": employee['full_name'],
                                    "employee_username": username_match,
                                    "ticket_subject": subject,
                                    "ticket_data": ticket_data,
                                    "employee_data": employee,
                                    "caller_name": st.session_state.username,
                                    "created_by": st.session_state.username
                                }
                                
                                # Create call notification in database for the assigned employee
                                success = db_manager.create_call_notification(
                                    target_employee=username_match,  # The ASSIGNED employee gets the call
                                    ticket_id=ticket_id,
                                    ticket_subject=subject,
                                    caller_name=st.session_state.username,
                                    call_info=call_info
                                )
                                
                                if success:
                                    assignment_response = f"Your ticket has been assigned to {employee['full_name']} ({employee['role_in_company']}). A voice call notification has been sent to {employee['full_name']}."
                                    st.session_state.ticket_manager.update_ticket_response(ticket_id, assignment_response)
                                    st.success(f"✅ Ticket assigned to {employee['full_name']}! Voice call notification sent.")
                                    st.info(f"📞 {employee['full_name']} will see an incoming call notification when they log in.")
                                else:
                                    assignment_response = f"Your ticket has been assigned to {employee['full_name']} ({employee['role_in_company']}). Please contact them directly."
                                    st.session_state.ticket_manager.update_ticket_response(ticket_id, assignment_response)
                                    st.warning("Ticket assigned but call notification failed.")
                            return
                
                # Regular AI response
                st.session_state.ticket_manager.update_ticket_response(ticket_id, response)
                st.success("✨ AI response generated and added to your ticket!")
            else:
                # Fallback response only if no AI response found
                response = "Thank you for your ticket. Our AI system has received your request and it will be reviewed shortly."
                st.session_state.ticket_manager.update_ticket_response(ticket_id, response)
                st.warning("AI response was empty, using fallback message.")
                
    except Exception as e:
        st.error(f"Error processing ticket with AI: {str(e)}")
        # Provide a basic response even if AI fails
        fallback_response = "Thank you for submitting your ticket. We have received your request and will respond as soon as possible."
        st.session_state.ticket_manager.update_ticket_response(ticket_id, fallback_response)

def show_user_tickets():
    """Display user's tickets."""
    # Header with refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### My Support Tickets")
    with col2:
        if st.button("🔄 Refresh Tickets", key="refresh_user_tickets", help="Refresh to see latest ticket updates"):
            st.rerun()
    
    tickets = st.session_state.ticket_manager.get_user_tickets(st.session_state.username)
    
    if not tickets:
        st.info("You haven't created any tickets yet. Use the 'Create Ticket' tab to submit your first support request.")
        return
    
    # Sort tickets by creation date (newest first)
    tickets.sort(key=lambda x: x["created_at"], reverse=True)
    
    for ticket in tickets:
        with st.expander(f"🎫 [{ticket['id']}] {ticket['subject']} - {ticket['status']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Category:** {ticket['category']}")
                st.write(f"**Priority:** {ticket['priority']}")
            
            with col2:
                st.write(f"**Status:** {ticket['status']}")
                st.write(f"**Created:** {format_datetime(ticket['created_at'])}")
            
            with col3:
                if ticket.get('assigned_to'):
                    employee = db_manager.get_employee_by_username(ticket['assigned_to'])
                    if employee:
                        st.write(f"**Assigned to:** {employee['full_name']}")
                        st.write(f"**Assignment Status:** {ticket.get('assignment_status', 'assigned').title()}")
                    else:
                        st.write(f"**Assigned to:** {ticket['assigned_to']}")
                elif ticket['response_at']:
                    st.write(f"**Responded:** {format_datetime(ticket['response_at'])}")
                else:
                    st.write("**Responded:** Pending")
            
            st.markdown("**Description:**")
            st.write(ticket['description'])
            
            if ticket.get('employee_solution'):
                st.markdown("**Solution:**")
                st.success(ticket['employee_solution'])
            elif ticket['response']:
                st.markdown("**AI Response:**")
                st.info(ticket['response'])
            else:
                if ticket.get('assigned_to'):
                    employee = db_manager.get_employee_by_username(ticket['assigned_to'])
                    employee_name = employee['full_name'] if employee else ticket['assigned_to']
                    st.warning(f"⏳ {employee_name} is working on your ticket...")
                else:
                    st.warning("⏳ Waiting for response...")

def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return datetime_str

def show_assigned_tickets():
    """Display tickets assigned to the current employee."""
    # Header with refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 👨‍💼 Tickets Assigned to Me")
    with col2:
        if st.button("🔄 Refresh Assignments", key="refresh_assigned_tickets", help="Refresh to see new ticket assignments"):
            st.rerun()
    
    assigned_tickets = st.session_state.ticket_manager.get_assigned_tickets(st.session_state.username)
    
    if not assigned_tickets:
        st.info("No tickets are currently assigned to you.")
        return
    
    # Sort tickets by assignment date (newest first)
    assigned_tickets.sort(key=lambda x: x.get("assignment_date", ""), reverse=True)
    
    for ticket in assigned_tickets:
        status_color = {
            "assigned": "🟡",
            "in_progress": "🔵", 
            "completed": "🟢"
        }.get(ticket.get("assignment_status", "assigned"), "⚪")
        
        with st.expander(f"{status_color} [{ticket['id']}] {ticket['subject']} - {ticket.get('assignment_status', 'assigned').title()}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**From:** {ticket['user']}")
                st.write(f"**Category:** {ticket['category']}")
                st.write(f"**Priority:** {ticket['priority']}")
                st.write(f"**Assigned:** {format_datetime(ticket.get('assignment_date', ''))}")
            
            with col2:
                st.write(f"**Status:** {ticket.get('assignment_status', 'assigned').title()}")
                if ticket.get('completion_date'):
                    st.write(f"**Completed:** {format_datetime(ticket['completion_date'])}")
            
            st.markdown("**Description:**")
            st.write(ticket['description'])
            
            # Solution form for employees
            if ticket.get('assignment_status') != 'completed':
                st.markdown("**Provide Solution:**")
                solution_key = f"solution_{ticket['id']}"
                solution = st.text_area(
                    "Your solution:",
                    placeholder="Provide a detailed solution to the user's issue...",
                    height=150,
                    key=solution_key
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Submit Solution", key=f"submit_{ticket['id']}"):
                        # Mark interaction time to prevent auto-refresh disruption
                        st.session_state._form_interaction_time = time.time()
                        if solution.strip():
                            st.session_state.ticket_manager.update_employee_solution(ticket['id'], solution.strip())
                            st.success("✅ Solution submitted successfully!")
                            st.rerun()
                        else:
                            st.error("Please provide a solution before submitting.")
                
                with col2:
                    if st.button(f"Mark In Progress", key=f"progress_{ticket['id']}"):
                        # Mark interaction time to prevent auto-refresh disruption
                        st.session_state._form_interaction_time = time.time()
                        # Update assignment status to in_progress
                        tickets = st.session_state.ticket_manager.load_tickets()
                        for t in tickets:
                            if t["id"] == ticket['id']:
                                t["assignment_status"] = "in_progress"
                                t["updated_at"] = datetime.now().isoformat()
                                break
                        st.session_state.ticket_manager.save_tickets(tickets)
                        st.success("✅ Ticket marked as in progress!")
                        st.rerun()
                
                with col3:
                    if st.button(f"📞 Call About This", key=f"call_{ticket['id']}"):
                        # Mark interaction time to prevent auto-refresh disruption
                        st.session_state._form_interaction_time = time.time()
                        # Create call notification for the current employee (self-call)
                        employee = db_manager.get_employee_by_username(st.session_state.username)
                        if employee:
                            call_info = {
                                "ticket_id": ticket['id'],
                                "employee_name": employee['full_name'],
                                "employee_username": st.session_state.username,
                                "ticket_subject": ticket['subject'],
                                "ticket_data": ticket,
                                "employee_data": employee,
                                "caller_name": "Self-Call",
                                "created_by": st.session_state.username
                            }
                            
                            # Create call notification for the current employee
                            success = db_manager.create_call_notification(
                                target_employee=st.session_state.username,
                                ticket_id=ticket['id'],
                                ticket_subject=ticket['subject'],
                                caller_name="Self-Call",
                                call_info=call_info
                            )
                            
                            if success:
                                st.success("📞 Voice call initiated! Check the sidebar to answer.")
                                st.rerun()
                            else:
                                st.error("Failed to start voice call.")
                        else:
                            st.error("Employee data not found.")
            else:
                st.markdown("**Your Solution:**")
                st.success(ticket.get('employee_solution', 'No solution provided'))

def show_active_call_interface():
    """Display the active voice call interface."""
    call_info = st.session_state.call_info
    
    # Add custom CSS for call interface
    st.markdown("""
    <style>
    .call-interface {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Call header with animation
    st.markdown(f"""
    <div class='call-interface'>
        <h2>📞 Active Call</h2>
        <p><strong>Employee:</strong> {call_info.get('employee_name', 'Unknown')}</p>
        <p><strong>Ticket:</strong> {call_info.get('ticket_subject', 'No subject')}</p>
        <p><strong>Ticket ID:</strong> {call_info.get('ticket_id', 'Unknown')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Play ringtone sound when call starts
    if "call_sound_played" not in st.session_state:
        ringtone_path = Path(__file__).parent.parent / "media" / "old_phone.mp3"
        if ringtone_path.exists():
            try:
                with open(ringtone_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                import base64
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                st.markdown(f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
                """, unsafe_allow_html=True)
                st.session_state.call_sound_played = True
            except Exception as e:
                print(f"Could not play ringtone: {e}")
    
    # Initialize vocal chat if not exists
    if not st.session_state.vocal_chat:
        from vocal_components import SmoothVocalChat
        st.session_state.vocal_chat = SmoothVocalChat()
    
    # Voice interface
    st.markdown("### 🎤 Voice Conversation")
    st.markdown("Speak into the microphone to discuss the ticket with the employee.")
    
    # Import audio recorder
    try:
        from audio_recorder_streamlit import audio_recorder
        
        # Audio recorder
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#ff4444",
            neutral_color="#28a745",
            icon_name="microphone",
            icon_size="3x",
            pause_threshold=2.0,
            sample_rate=41000,
            key="call_audio_recorder"
        )
        
        # Process audio input
        if audio_bytes:
            audio_hash = hash(audio_bytes)
            last_hash = st.session_state.get('last_call_audio_hash', None)
            
            if audio_hash != last_hash:
                st.session_state.last_call_audio_hash = audio_hash
                
                with st.spinner("🔄 Processing voice input..."):
                    # Get ticket and employee data
                    ticket_data = call_info.get('ticket_data', {})
                    employee_data = call_info.get('employee_data', {})
                    
                    # Process voice input
                    transcription, response, tts_audio_bytes = st.session_state.vocal_chat.process_voice_input(
                        audio_bytes, 
                        ticket_data, 
                        employee_data, 
                        st.session_state.conversation_history
                    )
                    
                    if transcription and response:
                        # Add to conversation history
                        st.session_state.conversation_history.append(("You", transcription))
                        st.session_state.conversation_history.append(("Employee", response))
                        
                        # Show transcription
                        st.success(f"**You said:** {transcription}")
                        st.info(f"**Employee:** {response}")
                        
                        # Play employee response
                        if tts_audio_bytes:
                            st.audio(tts_audio_bytes, format='audio/mp3', autoplay=True)
                            
    except ImportError:
        st.error("Audio recording not available. Please install audio_recorder_streamlit.")
        st.code("pip install audio_recorder_streamlit")
    
    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("### 📝 Conversation History")
        with st.expander("View conversation", expanded=False):
            for speaker, message in st.session_state.conversation_history:
                icon = "🎧" if speaker == "You" else "👨‍💼"
                st.markdown(f"**{icon} {speaker}:** {message}")
    
    # Call controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📴 End Call", type="secondary", use_container_width=True):
            # Generate solution from conversation
            if st.session_state.conversation_history:
                generate_solution_from_call()
            else:
                st.session_state.call_active = False
                st.session_state.call_info = None
                st.session_state.conversation_history = []
                st.rerun()
    
    with col2:
        if st.button("⏸️ Hold Call", use_container_width=True):
            st.info("Call placed on hold. Use the sidebar to resume.")
            st.session_state.call_active = False
            # Keep call_info for resuming
            st.rerun()
    
    with col3:
        if st.button("📋 View Ticket", use_container_width=True):
            # Show ticket details
            ticket_data = call_info.get('ticket_data', {})
            if ticket_data:
                st.markdown("### 🎫 Ticket Details")
                st.write(f"**Subject:** {ticket_data.get('subject', 'N/A')}")
                st.write(f"**Description:** {ticket_data.get('description', 'N/A')}")
                st.write(f"**Priority:** {ticket_data.get('priority', 'N/A')}")
                st.write(f"**Category:** {ticket_data.get('category', 'N/A')}")

def generate_solution_from_call():
    """Generate a solution from the voice call conversation."""
    if not st.session_state.conversation_history:
        st.warning("No conversation to generate solution from.")
        return
    
    try:
        # Initialize vocal chat if needed
        if not st.session_state.vocal_chat:
            from vocal_components import SmoothVocalChat
            st.session_state.vocal_chat = SmoothVocalChat()
        
        call_info = st.session_state.call_info
        ticket_data = call_info.get('ticket_data', {})
        employee_data = call_info.get('employee_data', {})
        
        # Generate solution from conversation
        conversation_summary = "\n".join([f"{speaker}: {message}" for speaker, message in st.session_state.conversation_history])
        
        with st.spinner("🔄 Generating solution from conversation..."):
            solution = st.session_state.vocal_chat.gemini.chat(
                f"Generate a professional ticket resolution based on this conversation: {conversation_summary}",
                ticket_data,
                employee_data,
                is_employee=False
            )
        
        if solution:
            # Update ticket with solution
            ticket_id = call_info.get('ticket_id')
            if ticket_id:
                st.session_state.ticket_manager.update_employee_solution(ticket_id, solution)
                st.success("✅ Solution generated and saved to ticket!")
                
                # Show the solution
                st.markdown("### 📝 Generated Solution")
                st.success(solution)
            else:
                st.error("Could not save solution: No ticket ID found.")
        else:
            st.error("Failed to generate solution from conversation.")
    
    except Exception as e:
        st.error(f"Error generating solution: {str(e)}")
    
    finally:
        # End the call
        st.session_state.call_active = False
        st.session_state.call_info = None
        st.session_state.conversation_history = []
        st.rerun()
"""
Ticket system component for Streamlit app.
Handles ticket creation, status tracking, and response management.
"""

import streamlit as st
import sys
import json
import uuid
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
    
    # Status selection (only for registered employees)
    employee = db_manager.get_employee_by_username(username)
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
            "response_at": None
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

def show_ticket_interface():
    """Display the main ticket interface."""
    # Render availability status in sidebar first
    render_availability_status()
    
    # Header with user info and logout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show enhanced user information
        user_display = st.session_state.get("user_full_name", st.session_state.username)
        user_role = st.session_state.get("user_role", "User")
        st.title(f"🎫 Support Ticket System")
        st.markdown(f"**Welcome {user_display}** | *{user_role}*")
    
    with col2:
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
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📝 Create Ticket", "📋 My Tickets"])
    
    with tab1:
        show_create_ticket_form()
    
    with tab2:
        show_user_tickets()

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
                # Update ticket with actual AI response
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
    st.markdown("### My Support Tickets")
    
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
                if ticket['response_at']:
                    st.write(f"**Responded:** {format_datetime(ticket['response_at'])}")
                else:
                    st.write("**Responded:** Pending")
            
            st.markdown("**Description:**")
            st.write(ticket['description'])
            
            if ticket['response']:
                st.markdown("**AI Response:**")
                st.info(ticket['response'])
            else:
                st.warning("⏳ Waiting for response...")

def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return datetime_str
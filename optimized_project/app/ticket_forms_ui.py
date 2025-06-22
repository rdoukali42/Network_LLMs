"""
Ticket forms and display components for the Optimized Streamlit app.
Handles UI for ticket creation, viewing user's tickets, and viewing assigned tickets.
"""

import streamlit as st
import time
from datetime import datetime
from typing import Any, Optional, Dict, List # For type hinting
from pathlib import Path

# Assuming this file is in optimized_project/app/
OPTIMIZED_PROJECT_ROOT_TF_UI = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT_TF_UI) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT_TF_UI))

from config import app_config # For session keys
# Dependencies (TicketManager, DatabaseManager, AppWorkflowClient) will be passed as arguments
# or retrieved from session state where they are initialized by a higher-level UI component (e.g., tickets_ui.py)

# Import the AI processing logic (which will be in its own file)
from .ticket_processing_ui import process_ticket_with_ai_and_notify # Adjusted name


# Helper to get TicketManager instance from session state (initialized in tickets_ui.py)
def _get_ticket_manager() -> Optional[Any]:
    return st.session_state.get(app_config.SESSION_KEYS["ticket_manager"])

# Helper to get DatabaseManager instance from session state (initialized in tickets_ui.py or auth.py)
def _get_db_manager() -> Optional[Any]:
    # This might be better if db_manager is consistently passed or set up once globally for UI
    if "db_manager_instance_ui" not in st.session_state: # Example session key for UI db manager
        from data_management.database import DatabaseManager # Fallback init, not ideal
        st.session_state.db_manager_instance_ui = DatabaseManager(project_root_path=OPTIMIZED_PROJECT_ROOT_TF_UI)
    return st.session_state.db_manager_instance_ui

# Helper to get AppWorkflowClient instance from session state (initialized in tickets_ui.py)
def _get_workflow_client() -> Optional[Any]:
    return st.session_state.get(app_config.SESSION_KEYS["workflow_client"])

def _format_datetime_display(datetime_str: Optional[str]) -> str:
    """Safely formats an ISO datetime string for display."""
    if not datetime_str: return "N/A"
    try:
        return datetime.fromisoformat(datetime_str).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return str(datetime_str) # Return as is if not parsable


def show_create_ticket_form_ui():
    """Displays the UI form for creating a new support ticket."""
    st.header("📝 Create New Support Ticket")

    ticket_manager = _get_ticket_manager()
    workflow_client = _get_workflow_client()

    if not ticket_manager:
        st.error("TicketManager not available. Cannot create tickets.")
        return
    if not workflow_client or not workflow_client.is_ai_system_ready():
        st.warning("AI Workflow Client not ready. Ticket will be created but not immediately processed by AI.")
        # Allow ticket creation, but AI processing might fail or be skipped in process_ticket_with_ai_and_notify

    current_username = st.session_state.get(app_config.SESSION_KEYS["username"])
    if not current_username:
        st.error("User not logged in. Cannot create tickets.")
        return

    with st.form("new_ticket_form_optimized"):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category",
                                    ["Technical Issue", "Feature Request", "Bug Report", "General Question", "Account Issue"],
                                    key="create_ticket_category")
        with col2:
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], index=1, key="create_ticket_priority")

        subject = st.text_input("Subject", placeholder="Brief summary of your issue", key="create_ticket_subject")
        description = st.text_area("Description", placeholder="Detailed information...", height=200, key="create_ticket_description")

        submitted = st.form_submit_button("Submit Ticket", use_container_width=True, type="primary")

        if submitted:
            st.session_state[app_config.SESSION_KEYS["_form_interaction_time"]] = time.time()

            # Prevent duplicate submissions logic
            form_unique_id = f"{category}-{priority}-{subject}-{description}"
            if form_unique_id == st.session_state.get(app_config.SESSION_KEYS["_last_form_submission"]):
                st.info("This ticket appears to be a duplicate of your last submission.")
                return

            if subject.strip() and description.strip():
                st.session_state[app_config.SESSION_KEYS["_last_form_submission"]] = form_unique_id

                ticket_id = ticket_manager.create_ticket(
                    user=current_username, category=category, priority=priority,
                    subject=subject.strip(), description=description.strip()
                )
                st.success(f"✅ Ticket created successfully! Ticket ID: **{ticket_id}**")
                st.info("Your ticket is being submitted for AI processing. Check 'My Tickets' for updates.")

                # Trigger AI processing (this function will handle notifications)
                # Pass workflow_client and ticket_manager to it.
                process_ticket_with_ai_and_notify(
                    ticket_id=ticket_id,
                    subject=subject.strip(),
                    description=description.strip(),
                    ticket_manager=ticket_manager,
                    workflow_client=workflow_client,
                    db_manager=_get_db_manager(), # For call notifications if assigned by AI
                    current_user_username=current_username
                )
                # Consider st.rerun() here if immediate feedback from AI processing is desired on this page,
                # or let smart refresh handle updates on the "My Tickets" tab.
            else:
                st.error("Please provide both a subject and a description for your ticket.")


def show_user_tickets_ui():
    """Displays tickets created by the current user."""
    st.header("📋 My Support Tickets")
    if st.button("🔄 Refresh My Tickets", key="refresh_my_tickets_btn"): st.rerun()

    ticket_manager = _get_ticket_manager()
    db_manager = _get_db_manager() # For fetching assigned employee names
    current_username = st.session_state.get(app_config.SESSION_KEYS["username"])

    if not ticket_manager or not db_manager or not current_username:
        st.error("Required services (TicketManager, DatabaseManager) or user session not available.")
        return

    user_tickets = ticket_manager.get_user_tickets(current_username)
    if not user_tickets:
        st.info("You haven't created any tickets yet. Use the 'Create Ticket' tab to submit one!"); return

    user_tickets.sort(key=lambda t: t.get("created_at", ""), reverse=True)

    for ticket in user_tickets:
        exp_title = f"🎫 [{ticket.get('id','N/A')}] {ticket.get('subject','No Subject')} - Status: {ticket.get('status','N/A')}"
        with st.expander(exp_title):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Category:** {ticket.get('category', 'N/A')}")
                st.write(f"**Priority:** {ticket.get('priority', 'N/A')}")
            with col2:
                st.write(f"**Created:** {_format_datetime_display(ticket.get('created_at'))}")
                st.write(f"**Last Updated:** {_format_datetime_display(ticket.get('updated_at'))}")
            with col3:
                assigned_to_username = ticket.get('assigned_to')
                if assigned_to_username:
                    emp = db_manager.get_employee_by_username(assigned_to_username)
                    st.write(f"**Assigned to:** {emp['full_name'] if emp else assigned_to_username}")
                    st.write(f"**Assignment Status:** {ticket.get('assignment_status', 'N/A').title()}")
                elif ticket.get('response_at'):
                    st.write(f"**AI Responded:** {_format_datetime_display(ticket.get('response_at'))}")
                else:
                    st.write("**Response:** Pending")

            st.markdown(f"**Description:**\n{ticket.get('description', 'N/A')}")

            if ticket.get('employee_solution'):
                st.markdown("**Provided Solution:**"); st.success(ticket['employee_solution'])
            elif ticket.get('response'):
                st.markdown("**AI Response:**"); st.info(ticket['response'])
            elif ticket.get('assigned_to'):
                emp_name = db_manager.get_employee_by_username(ticket['assigned_to'])['full_name'] if db_manager.get_employee_by_username(ticket['assigned_to']) else ticket['assigned_to']
                st.warning(f"⏳ {emp_name} is working on your ticket...")
            else:
                st.warning("⏳ Waiting for initial processing or assignment...")


def show_assigned_tickets_ui():
    """Displays tickets assigned to the currently logged-in employee."""
    st.header("👨‍💼 Tickets Assigned to Me")
    if st.button("🔄 Refresh Assigned Tickets", key="refresh_assigned_btn"): st.rerun()

    ticket_manager = _get_ticket_manager()
    db_manager = _get_db_manager()
    current_username = st.session_state.get(app_config.SESSION_KEYS["username"])

    if not ticket_manager or not db_manager or not current_username:
        st.error("Required services or user session not available."); return

    assigned_tickets = ticket_manager.get_assigned_tickets(current_username)
    if not assigned_tickets:
        st.info("No tickets are currently assigned to you."); return

    assigned_tickets.sort(key=lambda t: t.get("assignment_date", ""), reverse=True)
    status_color_map = {"assigned": "🟡", "in_progress": "🔵", "completed": "🟢"}

    for ticket in assigned_tickets:
        assign_status = ticket.get("assignment_status", "assigned")
        exp_title = f"{status_color_map.get(assign_status, '⚪')} [{ticket.get('id')}] {ticket.get('subject')} - Status: {assign_status.title()}"

        with st.expander(exp_title):
            col_details1, col_details2 = st.columns(2)
            with col_details1:
                st.write(f"**From User:** {ticket.get('user')}")
                st.write(f"**Category:** {ticket.get('category')}")
                st.write(f"**Priority:** {ticket.get('priority')}")
            with col_details2:
                st.write(f"**Assigned:** {_format_datetime_display(ticket.get('assignment_date'))}")
                if ticket.get('completion_date'):
                    st.write(f"**Completed:** {_format_datetime_display(ticket.get('completion_date'))}")

            st.markdown(f"**Description:**\n{ticket.get('description')}")

            if assign_status != 'completed':
                st.markdown("**Provide Solution / Update Status:**")
                solution_key = f"solution_text_{ticket.get('id')}"
                current_solution_text = st.text_area("Your Solution / Notes:", height=150, key=solution_key,
                                                     value=ticket.get('employee_solution', ''))

                btn_cols = st.columns(3)
                with btn_cols[0]:
                    if st.button("✅ Submit Solution & Complete", key=f"submit_solution_{ticket.get('id')}", type="primary"):
                        st.session_state[app_config.SESSION_KEYS["_form_interaction_time"]] = time.time()
                        if current_solution_text.strip():
                            ticket_manager.update_employee_solution(ticket.get('id'), current_solution_text.strip())
                            st.success("Solution submitted and ticket marked completed!"); st.rerun()
                        else:
                            st.error("Please provide a solution text.")
                with btn_cols[1]:
                    if assign_status != "in_progress":
                        if st.button("▶️ Mark In Progress", key=f"mark_progress_{ticket.get('id')}"):
                            st.session_state[app_config.SESSION_KEYS["_form_interaction_time"]] = time.time()
                            ticket_manager.update_assignment_status(ticket.get('id'), "in_progress")
                            st.success("Ticket marked as 'In Progress'."); st.rerun()
                with btn_cols[2]:
                    if st.button("📞 Start Voice Call (Self)", key=f"self_call_{ticket.get('id')}"):
                        st.session_state[app_config.SESSION_KEYS["_form_interaction_time"]] = time.time()
                        employee_data = db_manager.get_employee_by_username(current_username)
                        if employee_data:
                            call_payload = {
                                "ticket_id": ticket.get('id'), "employee_name": employee_data['full_name'],
                                "employee_username": current_username, "ticket_subject": ticket.get('subject'),
                                "ticket_data_snapshot": ticket, "employee_data_snapshot": employee_data,
                                "caller_name": "Self (Working on Ticket)", "created_by": current_username
                            }
                            if db_manager.create_call_notification(current_username, ticket.get('id'), ticket.get('subject'), "Self", call_payload):
                                st.success("Voice call initiated for you. Check sidebar to answer."); st.rerun()
                            else: st.error("Failed to initiate self-call notification.")
                        else: st.error("Could not retrieve your employee data to start call.")
            else: # Completed
                st.markdown("**Your Solution:**"); st.success(ticket.get('employee_solution', 'N/A'))

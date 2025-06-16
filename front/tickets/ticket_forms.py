"""
Ticket forms and display components.
Handles ticket creation and display interfaces.
"""

import streamlit as st
import time
from datetime import datetime
from database import db_manager


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
            
            # Prevent duplicate processing by checking if this is a new submission
            current_form_key = f"{category}_{priority}_{subject}_{description}"
            last_form_key = st.session_state.get('_last_form_submission', '')
            
            if subject.strip() and description.strip() and current_form_key != last_form_key:
                # Store this submission to prevent duplicates
                st.session_state._last_form_submission = current_form_key
                
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
                from .ticket_processing import process_ticket_with_ai
                process_ticket_with_ai(ticket_id, subject, description)
                
            elif current_form_key == last_form_key:
                st.info("This ticket was already submitted. Please check the 'My Tickets' tab.")
            else:
                st.error("Please fill in both subject and description fields.")


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


def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display."""
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return datetime_str

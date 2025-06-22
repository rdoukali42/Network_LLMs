"""
AI ticket processing logic for the Optimized Streamlit app.
This module is called after a ticket is created to interact with the AI backend.
"""

import streamlit as st
from typing import Any, Dict, Optional # For type hinting
from pathlib import Path

# Assuming this file is in optimized_project/app/
OPTIMIZED_PROJECT_ROOT_TP_UI = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT_TP_UI) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT_TP_UI))

# Dependencies will be passed as arguments:
# from .workflow_client import AppWorkflowClient
# from data_management.ticket_store import TicketManager
# from data_management.database import DatabaseManager
# from config import app_config # For session keys if needed directly, though username passed

def process_ticket_with_ai_and_notify(
    ticket_id: str,
    subject: str,
    description: str,
    ticket_manager: Any,      # Instance of TicketManager
    workflow_client: Any,   # Instance of AppWorkflowClient
    db_manager: Any,          # Instance of DatabaseManager
    current_user_username: str # Username of the user who created the ticket
):
    """
    Processes a newly created ticket using the AI workflow and updates the ticket accordingly.
    Handles notifications to the user via st.success/st.info/st.warning/st.error.
    Args:
        ticket_id: The ID of the newly created ticket.
        subject: The subject of the ticket.
        description: The description of the ticket.
        ticket_manager: Instance of TicketManager.
        workflow_client: Instance of AppWorkflowClient for AI processing.
        db_manager: Instance of DatabaseManager for employee lookups and call notifications.
        current_user_username: The username of the user who submitted the ticket (for self-assignment check).
    """

    if not workflow_client or not workflow_client.is_ai_system_ready():
        st.warning("AI system is not ready. Ticket will be queued for later processing if applicable, or please try again later.")
        # Optionally, update ticket status to something like "Pending AI Processing"
        ticket_manager.update_ticket(ticket_id, {"status": "Pending AI Processing", "response": "AI system offline during submission."})
        return

    formatted_query = f"Support Ticket Request:\nSubject: {subject}\nDescription: {description}"

    # Context for AI System, especially for HR agent to exclude ticket submitter
    additional_context_for_ai = {
        "exclude_username": current_user_username,
        "ticket_id": ticket_id # Pass ticket_id for traceability in backend/Langfuse
    }

    with st.spinner(f"Ticket {ticket_id} is being analyzed by AI..."):
        try:
            # Call the AI system via the workflow client
            ai_system_response = workflow_client.process_message(
                message_text=formatted_query,
                additional_context=additional_context_for_ai
            )

            if ai_system_response.get("status") == "error":
                st.error(f"AI processing error: {ai_system_response.get('error', 'Unknown error')}")
                ticket_manager.update_ticket(ticket_id, {"response": f"AI Error: {ai_system_response.get('error')}", "status": "Error Processing"})
                return

            # Extract structured data from the AI system's response
            # The AISystem response structure is:
            # { "query": ..., "status": ..., "result": final_response_text, "synthesis": ...,
            #   "workflow_full_output": { ... graph results ...} }

            final_ai_text_response = ai_system_response.get("synthesis", "AI processing complete. Awaiting review.")
            workflow_details = ai_system_response.get("workflow_full_output", {}) # This contains agent outputs

            # Check for HR assignment action from the workflow details
            # The workflow saves HR action and employee data in state["results"]
            # This structure depends on how MultiAgentWorkflow and HRAgent populate it.
            # Assuming HRAgent's output (HRTicketResponse model) is nested in workflow_details["hr_assignment_output"]

            hr_assignment_details = workflow_details.get("hr_assignment_output")
            # print(f"DEBUG ticket_processing_ui: hr_assignment_details = {hr_assignment_details}")

            # Check if hr_assignment_details is a dict and has 'status' and 'recommended_assignment'
            # This aligns with HRAgent returning HRTicketResponse.model_dump()
            is_successful_hr_assignment = False
            assigned_employee_username = None
            assigned_employee_details = None # This would be the HREmployeeMatch model data

            if isinstance(hr_assignment_details, dict) and \
               hr_assignment_details.get("status") == "success" and \
               hr_assignment_details.get("recommended_assignment"):

                recommended_emp_id = hr_assignment_details["recommended_assignment"]
                matched_employees_list = hr_assignment_details.get("matched_employees", [])

                for emp_match_data in matched_employees_list:
                    if emp_match_data.get("employee_id") == recommended_emp_id:
                        assigned_employee_details = emp_match_data # This is HREmployeeMatch data
                        assigned_employee_username = emp_match_data.get("username")
                        break

                if assigned_employee_username:
                    is_successful_hr_assignment = True


            if is_successful_hr_assignment and assigned_employee_username and assigned_employee_details:
                # Self-assignment check (already handled by AvailabilityTool exclusion, but good to double check)
                if assigned_employee_username == current_user_username:
                    st.warning(f"⚠️ AI attempted self-assignment to {assigned_employee_details.get('name', assigned_employee_username)}. This is not allowed. Ticket will be manually reviewed or reprocessed.")
                    ticket_manager.update_ticket(ticket_id, {"response": "Self-assignment prevented. Awaiting manual review.", "status": "Needs Review"})
                else:
                    # Assign ticket and create call notification
                    ticket_manager.assign_ticket(ticket_id, assigned_employee_username)

                    # Prepare call_info payload for DatabaseManager.create_call_notification
                    # This needs the full employee record from DB, not just HREmployeeMatch
                    full_employee_record_from_db = db_manager.get_employee_by_username(assigned_employee_username)
                    current_ticket_data = ticket_manager.get_ticket_by_id(ticket_id)

                    if full_employee_record_from_db and current_ticket_data:
                        call_info_payload = {
                            "ticket_id": ticket_id,
                            "employee_name": full_employee_record_from_db.get('full_name'),
                            "employee_username": assigned_employee_username,
                            "employee_data_snapshot": full_employee_record_from_db, # For VoiceService context
                            "ticket_subject": subject,
                            "ticket_data_snapshot": current_ticket_data, # For VoiceService context
                            "caller_name": current_user_username, # User who submitted the ticket
                            "created_by": "AISystemAssignment"
                        }
                        # Create notification for the ASSIGNED employee
                        call_notif_success = db_manager.create_call_notification(
                            target_employee=assigned_employee_username,
                            ticket_id=ticket_id,
                            ticket_subject=subject,
                            caller_name=current_user_username, # User who created the ticket
                            call_info=call_info_payload
                        )
                        assigned_emp_name = assigned_employee_details.get('name', assigned_employee_username)
                        assignment_msg = f"Ticket assigned to {assigned_emp_name}."
                        if call_notif_success:
                            assignment_msg += f" A voice call notification has been sent to them."
                            st.success(f"✅ {assignment_msg}")
                        else:
                            assignment_msg += f" Please contact them directly (call notification failed)."
                            st.warning(f"⚠️ {assignment_msg}")

                        ticket_manager.update_ticket(ticket_id, {"response": assignment_msg}) # Store this as the "AI response"
                    else:
                        st.error("Failed to retrieve full data for call notification after assignment.")
                        ticket_manager.update_ticket(ticket_id, {"response": "Assigned, but call notification data error."})
            else:
                # No HR assignment or HR assignment failed, use the general AI synthesis
                ticket_manager.update_ticket_response(ticket_id, final_ai_text_response)
                st.success("✨ AI analysis complete. Response added to your ticket.")
                if hr_assignment_details and hr_assignment_details.get("status") != "success":
                    st.warning(f"HR Agent Note: {hr_assignment_details.get('error_message', 'Could not find a suitable assignment.')}")


        except Exception as e:
            st.error(f"An unexpected error occurred during AI processing: {str(e)}")
            ticket_manager.update_ticket(ticket_id, {"response": f"Critical AI Processing Error: {str(e)}", "status": "Error Processing"})
            import traceback
            traceback.print_exc()

# This module primarily contains a function, not UI elements itself.
# It's called by ticket_forms_ui.py.

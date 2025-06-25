"""
AI ticket processing workflow module.
Handles AI-powered ticket analysis and assignment logic via the service layer.
"""

import streamlit as st
from database import db_manager


def process_ticket_with_ai(ticket_id: str, subject: str, description: str):
    """Process ticket with AI workflow via service layer."""
    try:
        # Get service integration instance
        service_integration = st.session_state.get("service_integration")
        if not service_integration:
            from service_integration import ServiceIntegration
            service_integration = ServiceIntegration()
            st.session_state.service_integration = service_integration
        
        # Combine subject and description for AI processing
        query = f"🎫 Support Ticket: {subject}\n📝 Ticket-Query: {description}\n"
        
        # Determine appropriate workflow type based on ticket content
        content = f"{subject} {description}".lower()
        hr_keywords = ['vacation', 'time off', 'leave', 'pto', 'sick', 'holiday', 'hr', 'human resources', 'payroll', 'benefits', 'policy']
        
        # Check if this is likely an HR request
        is_hr_request = any(keyword in content for keyword in hr_keywords)
        
        # Process with appropriate AI workflow via service layer
        with st.spinner(f"Processing ticket {ticket_id} with AI..."):
            if is_hr_request:
                # Use HR workflow for HR-related requests
                try:
                    workflow_service = service_integration.service_manager.get_service('workflow')
                    # Import WorkflowType properly
                    import sys
                    sys.path.append('..')
                    sys.path.append('../src')
                    from services.workflow_service import WorkflowType
                    workflow_id = workflow_service.start_workflow(
                        workflow_type=WorkflowType.HR_REQUEST,
                        username=st.session_state.get('username', 'anonymous'),
                        input_data={"query": query, "original_ticket_id": ticket_id},
                        ticket_id=ticket_id
                    )
                    # Get the result
                    workflow_status = workflow_service.get_workflow_status(workflow_id)
                    result = {
                        "workflow_result": workflow_status.get("output_data", {}) if workflow_status else {},
                        "result": workflow_status.get("output_data", {}).get("response", "HR request processed") if workflow_status else "HR request processed"
                    }
                except Exception as e:
                    # Fallback to general workflow if HR workflow fails
                    print(f"HR workflow failed, using fallback: {e}")
                    result = service_integration.process_workflow_query(query)
            else:
                # Use general query answering workflow
                result = service_integration.process_workflow_query(query, ticket_id=ticket_id)
            
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
                
            # Check for structured assignment data from workflow first
            workflow_result = result.get("workflow_result", {}) if isinstance(result, dict) else {}
            hr_action = workflow_result.get("hr_action")
            employee_data = workflow_result.get("employee_data")

            if hr_action == "assign" and employee_data:
                username_match = employee_data.get("username")
                
                if username_match:
                    # Verify employee exists
                    employee = db_manager.get_employee_by_username(username_match)
                    if employee:
                        # Prevent self-assignment: check if the assigned employee username matches the ticket submitter
                        if username_match == st.session_state.username:
                            # Skip this assignment and provide a message indicating the need for alternative routing
                            fallback_response = f"The system attempted to assign this ticket to {employee['full_name']}, but automatic self-assignment is not allowed. Your ticket will be reviewed and manually assigned to an appropriate expert."
                            st.session_state.ticket_manager.update_ticket_response(ticket_id, fallback_response)
                            st.warning(f"⚠️ Self-assignment prevented: {employee['full_name']} cannot be assigned to their own ticket.")
                            return
                        
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
            
            # Fallback: Check if this is an HR referral with emoji pattern (legacy support)
            if response and response.strip():
                if "👤" in response and "(@" in response and "🏢 **Role**:" in response:
                    # Parse employee username from response
                    username_match = response.split("(@")[1].split(")")[0] if "(@" in response else None
                    
                    if username_match:
                        # Verify employee exists
                        employee = db_manager.get_employee_by_username(username_match)
                        if employee:
                            # Prevent self-assignment: check if the assigned employee username matches the ticket submitter
                            if username_match == st.session_state.username:
                                # Skip this assignment and provide a message indicating the need for alternative routing
                                fallback_response = f"The system attempted to assign this ticket to {employee['full_name']}, but automatic self-assignment is not allowed. Your ticket will be reviewed and manually assigned to an appropriate expert."
                                st.session_state.ticket_manager.update_ticket_response(ticket_id, fallback_response)
                                st.warning(f"⚠️ Self-assignment prevented: {employee['full_name']} cannot be assigned to their own ticket.")
                                return
                            
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

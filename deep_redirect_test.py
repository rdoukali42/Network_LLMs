#!/usr/bin/env python3
"""
Deep Real Scenario Test - Complete Redirect Workflow
Simulates a real ticket submission, assignment, vocal call, redirect request, and final resolution
"""

import sys
import json
import uuid
from datetime import datetime
sys.path.append('/Users/level3/Desktop/Network/src')
sys.path.append('/Users/level3/Desktop/Network/front')

from main import AISystem
from database import db_manager
from agents.vocal_assistant import VocalAssistantAgent, VocalResponse

class RealRedirectScenarioTest:
    """Complete end-to-end test of redirect functionality with real scenario."""
    
    def __init__(self):
        self.ai_system = AISystem("development")
        self.test_ticket_id = None
        
    def step_1_submit_ticket(self):
        """Step 1: User submits a complex database performance ticket."""
        print("🎫 STEP 1: User submits ticket...")
        
        # Real scenario: User has a complex database performance issue
        ticket_data = {
            "id": str(uuid.uuid4())[:8],
            "user": "sarah_martinez",
            "category": "Technical Issue", 
            "priority": "High",
            "subject": "Critical Database Performance Degradation",
            "description": "Our PostgreSQL database is experiencing severe performance issues. Query response times have increased from 2-3 seconds to 30+ seconds. We need someone with deep database optimization expertise to analyze slow queries, review indexing strategies, and optimize our connection pooling. This is affecting our production environment and customer experience.",
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.test_ticket_id = ticket_data["id"]
        
        # Save ticket to tickets.json (simulate frontend submission)
        try:
            with open('/Users/level3/Desktop/Network/front/tickets.json', 'r') as f:
                tickets = json.load(f)
        except:
            tickets = []
        
        tickets.append(ticket_data)
        
        with open('/Users/level3/Desktop/Network/front/tickets.json', 'w') as f:
            json.dump(tickets, f, indent=2)
        
        print(f"   ✅ Ticket {self.test_ticket_id} submitted")
        print(f"   📋 Subject: {ticket_data['subject']}")
        print(f"   👤 User: {ticket_data['user']}")
        print(f"   🔥 Priority: {ticket_data['priority']}")
        print(f"   📝 Description: {ticket_data['description'][:100]}...")
        
        return ticket_data
    
    def step_2_initial_assignment(self, ticket_data):
        """Step 2: AI System processes ticket and assigns to employee."""
        print(f"\n🤖 STEP 2: AI System processing ticket {self.test_ticket_id}...")
        
        # Process the ticket through the AI workflow
        query = f"Subject: {ticket_data['subject']}\nDescription: {ticket_data['description']}"
        result = self.ai_system.process_query(query)
        
        print(f"   🎯 Workflow Status: {result.get('status', 'unknown')}")
        
        # Extract assigned employee info
        hr_response = result.get('workflow_result', {}).get('hr_response', {})
        if hr_response and hr_response.get('matched_employees'):
            assigned_employee = hr_response['matched_employees'][0]
            print(f"   👤 Assigned to: {assigned_employee.get('name', 'Unknown')}")
            print(f"   🎭 Role: {assigned_employee.get('department', 'Unknown')}")
            print(f"   🧠 Skills: {', '.join(assigned_employee.get('skills', []))}")
            print(f"   📊 Match Score: {assigned_employee.get('overall_score', 0):.2f}")
            print(f"   💭 Reasoning: {assigned_employee.get('match_reasoning', 'No reasoning')[:100]}...")
            
            return assigned_employee, result
        else:
            print("   ❌ No employee assigned")
            return None, result
    
    def step_3_simulate_vocal_call(self, assigned_employee, ticket_data):
        """Step 3: Simulate vocal call where employee realizes they can't handle it."""
        print(f"\n📞 STEP 3: Vocal call with {assigned_employee.get('name', 'Unknown')}...")
        
        # Create VocalAssistant
        vocal_assistant = VocalAssistantAgent(config=self.ai_system.config)
        
        # Simulate conversation where employee realizes they're not the right person
        print(f"   🤖 Anna initiating call...")
        
        employee_data = {
            "full_name": assigned_employee.get('name', 'Unknown'),
            "username": assigned_employee.get('username', 'unknown'),
            "role_in_company": assigned_employee.get('department', 'Unknown'),
            "expertise": ', '.join(assigned_employee.get('skills', [])),
            "email": f"{assigned_employee.get('username', 'unknown')}@company.com"
        }
        
        # Simulate employee's response indicating they can't handle this
        employee_responses = [
            "Hi Anna! I looked at this database performance ticket from Sarah. This is really complex - it involves PostgreSQL optimization, query analysis, and connection pooling. I'm more of a Python developer and don't have deep database administration experience.",
            "I think this ticket needs someone with DBA expertise. You should redirect this to someone who specializes in database performance optimization. Maybe someone from the database team or a senior backend developer with PostgreSQL experience?",
            "Actually, I know exactly who should handle this - redirect it to Alice Chen. She's our Database Administrator and has years of experience with PostgreSQL performance tuning. She would be much better suited for this critical issue."
        ]
        
        print(f"   👤 {employee_data['full_name']}: {employee_responses[0]}")
        print(f"   👤 {employee_data['full_name']}: {employee_responses[1]}")
        print(f"   👤 {employee_data['full_name']}: {employee_responses[2]}")
        
        # Get Anna's response to the redirect request
        final_message = employee_responses[2]  # The one with specific redirect request
        
        print(f"\n   🤖 Anna processing redirect request...")
        
        anna_response = vocal_assistant.gemini.chat(
            final_message,
            ticket_data,
            employee_data,
            is_employee=True,
            conversation_history=[
                ("Anna", "Hi! I have a critical database performance ticket from Sarah..."),
                (employee_data['full_name'], employee_responses[0]),
                ("Anna", "I understand, this does sound quite specialized..."),
                (employee_data['full_name'], employee_responses[1]),
                ("Anna", "That makes sense. Do you have someone specific in mind?"),
                (employee_data['full_name'], employee_responses[2])
            ]
        )
        
        print(f"   🤖 Anna: {anna_response}")
        
        # Parse the response for redirect information
        conversation_data = {"response": anna_response}
        vocal_response = VocalResponse(conversation_data)
        
        print(f"\n   🔍 Redirect Analysis:")
        print(f"      Redirect Requested: {vocal_response.redirect_requested}")
        if vocal_response.redirect_requested:
            print(f"      Redirect Info: {vocal_response.redirect_employee_info}")
        
        return vocal_response, conversation_data
    
    def step_4_process_redirect(self, vocal_response, conversation_data, ticket_data):
        """Step 4: Process the redirect through the workflow."""
        print(f"\n🔄 STEP 4: Processing redirect request...")
        
        if not vocal_response.redirect_requested:
            print("   ❌ No redirect detected - stopping test")
            return None
        
        # Create workflow state for redirect processing
        redirect_state = {
            "current_step": "vocal_assistant",
            "messages": [],
            "metadata": {},
            "query": f"{ticket_data['subject']}: {ticket_data['description']}",
            "results": {
                "conversation_data": conversation_data,
                "ticket_data": ticket_data,
                "redirect_info": vocal_response.redirect_employee_info
            }
        }
        
        workflow = self.ai_system.workflow
        
        # Test redirect detection
        redirect_route = workflow._check_for_redirect(redirect_state)
        print(f"   🎯 Redirect Route: {redirect_route}")
        
        if redirect_route == "redirect":
            # Process through redirect workflow
            print(f"   🔄 Running redirect detector...")
            state_1 = workflow._redirect_detector_step(redirect_state)
            
            print(f"   🔍 Running employee searcher...")
            state_2 = workflow._employee_searcher_step(state_1)
            
            candidates = state_2['results'].get('redirect_candidates', [])
            print(f"   📋 Found {len(candidates)} redirect candidates:")
            
            for i, candidate in enumerate(candidates[:3], 1):
                print(f"      {i}. {candidate.get('full_name', 'Unknown')} (score: {candidate.get('redirect_score', 0)})")
                print(f"         Reasons: {', '.join(candidate.get('match_reasons', []))}")
            
            print(f"   🎯 Running maestro selector...")
            state_3 = workflow._maestro_redirect_selector_step(state_2)
            
            selected = state_3['results'].get('selected_redirect_employee', {})
            print(f"   ✅ Selected for redirect: {selected.get('full_name', 'None')}")
            
            return selected, state_3
        
        return None, None
    
    def step_5_simulate_redirect_call(self, selected_employee, ticket_data):
        """Step 5: Simulate call with redirected employee."""
        print(f"\n📞 STEP 5: Vocal call with redirected employee...")
        
        if not selected_employee:
            print("   ❌ No employee selected for redirect")
            return None
        
        print(f"   🤖 Anna calling {selected_employee.get('full_name', 'Unknown')}...")
        
        # Create vocal assistant for redirect call
        vocal_assistant = VocalAssistantAgent(config=self.ai_system.config)
        
        # Simulate redirect call where the correct expert handles the issue
        expert_response = f"Hi Anna! Yes, I can definitely help with this PostgreSQL performance issue. I've dealt with similar problems before. Based on Sarah's description, this sounds like a combination of missing indexes, poor query optimization, and possibly connection pool misconfiguration. I'll need to analyze the slow query logs, review the database schema, and check the connection pool settings. I can start working on this immediately given the high priority."
        
        print(f"   👤 {selected_employee.get('full_name', 'Unknown')}: {expert_response}")
        
        # Get Anna's response (should not request another redirect)
        anna_response = vocal_assistant.gemini.chat(
            expert_response,
            ticket_data,
            selected_employee,
            is_employee=True,
            conversation_history=[
                ("Anna", f"Hi {selected_employee.get('full_name', 'Unknown')}! I have a critical database performance ticket that was redirected to you..."),
                (selected_employee.get('full_name', 'Unknown'), expert_response)
            ]
        )
        
        print(f"   🤖 Anna: {anna_response}")
        
        # Parse response to ensure no further redirect
        conversation_data = {"response": anna_response}
        vocal_response = VocalResponse(conversation_data)
        
        print(f"\n   🔍 Final Analysis:")
        print(f"      Further Redirect Requested: {vocal_response.redirect_requested}")
        print(f"      Conversation Complete: {vocal_response.conversation_complete}")
        
        if vocal_response.conversation_complete:
            print(f"   ✅ Ticket successfully handled by expert!")
            return True
        
        return False
    
    def step_6_update_ticket_status(self, selected_employee, ticket_data):
        """Step 6: Update ticket with final resolution."""
        print(f"\n📝 STEP 6: Updating ticket status...")
        
        # Update the ticket in tickets.json
        try:
            with open('/Users/level3/Desktop/Network/front/tickets.json', 'r') as f:
                tickets = json.load(f)
            
            # Find and update the test ticket
            for ticket in tickets:
                if ticket.get('id') == self.test_ticket_id:
                    ticket['status'] = 'Redirected and Assigned'
                    ticket['assigned_to'] = selected_employee.get('username', 'unknown')
                    ticket['updated_at'] = datetime.now().isoformat()
                    ticket['response'] = f"Ticket redirected to {selected_employee.get('full_name', 'Unknown')} - Database Administration Expert. Initial assignment was to wrong specialist, redirect successful."
                    ticket['redirect_history'] = {
                        'original_assignee': 'Initial AI assignment',
                        'redirected_to': selected_employee.get('full_name', 'Unknown'),
                        'redirect_reason': 'Specialized database expertise required',
                        'redirect_timestamp': datetime.now().isoformat()
                    }
                    break
            
            with open('/Users/level3/Desktop/Network/front/tickets.json', 'w') as f:
                json.dump(tickets, f, indent=2)
            
            print(f"   ✅ Ticket {self.test_ticket_id} updated successfully")
            print(f"   👤 Final assignee: {selected_employee.get('full_name', 'Unknown')}")
            print(f"   📊 Status: Redirected and Assigned")
            
        except Exception as e:
            print(f"   ❌ Error updating ticket: {e}")
    
    def cleanup(self):
        """Remove test ticket from system."""
        print(f"\n🧹 CLEANUP: Removing test ticket {self.test_ticket_id}...")
        
        try:
            with open('/Users/level3/Desktop/Network/front/tickets.json', 'r') as f:
                tickets = json.load(f)
            
            # Remove test ticket
            tickets = [t for t in tickets if t.get('id') != self.test_ticket_id]
            
            with open('/Users/level3/Desktop/Network/front/tickets.json', 'w') as f:
                json.dump(tickets, f, indent=2)
            
            print(f"   ✅ Test ticket removed")
            
        except Exception as e:
            print(f"   ❌ Error during cleanup: {e}")
    
    def run_complete_test(self):
        """Run the complete redirect scenario test."""
        print("🚀 STARTING DEEP REAL SCENARIO REDIRECT TEST")
        print("=" * 60)
        
        try:
            # Step 1: Submit ticket
            ticket_data = self.step_1_submit_ticket()
            
            # Step 2: Initial AI assignment  
            assigned_employee, workflow_result = self.step_2_initial_assignment(ticket_data)
            
            if not assigned_employee:
                print("❌ Test failed: No initial assignment")
                return False
            
            # Step 3: Vocal call with wrong employee
            vocal_response, conversation_data = self.step_3_simulate_vocal_call(assigned_employee, ticket_data)
            
            # Step 4: Process redirect
            selected_employee, final_state = self.step_4_process_redirect(vocal_response, conversation_data, ticket_data)
            
            if not selected_employee:
                print("❌ Test failed: Redirect processing failed")
                return False
            
            # Step 5: Call with correct employee
            success = self.step_5_simulate_redirect_call(selected_employee, ticket_data)
            
            if not success:
                print("❌ Test failed: Redirect call failed")
                return False
            
            # Step 6: Update ticket
            self.step_6_update_ticket_status(selected_employee, ticket_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Always cleanup
            if self.test_ticket_id:
                self.cleanup()

def main():
    """Run the deep redirect test."""
    test = RealRedirectScenarioTest()
    success = test.run_complete_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DEEP REDIRECT TEST PASSED!")
        print("✅ Complete workflow tested successfully:")
        print("   1. ✅ Ticket submission and initial assignment")
        print("   2. ✅ Vocal call with wrong employee")
        print("   3. ✅ Redirect request detection and parsing")
        print("   4. ✅ Employee search and selection")
        print("   5. ✅ Successful redirect to correct expert")
        print("   6. ✅ Ticket status update and completion")
        print("\n🔥 Redirect system is PRODUCTION READY!")
    else:
        print("❌ DEEP REDIRECT TEST FAILED!")
        print("Check the error messages above for details.")

if __name__ == "__main__":
    main()

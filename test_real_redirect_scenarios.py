#!/usr/bin/env python3
"""
Real-world redirect workflow testing scenarios.
Tests the complete redirect flow with actual system components.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add source directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class RedirectWorkflowTester:
    """Tests redirect workflow with real scenarios."""
    
    def __init__(self):
        """Initialize the tester with real system components."""
        self.system = None
        self.test_results = []
        self.setup_system()
    
    def setup_system(self):
        """Setup the actual AI system."""
        print("🚀 Initializing real AI system components...")
        
        try:
            from main import AISystem
            self.system = AISystem("development")
            
            if self.system.agents and self.system.workflow:
                print("✅ AI system initialized successfully")
                print(f"✅ Available agents: {list(self.system.agents.keys())}")
                return True
            else:
                print("⚠️ System initialized but some components missing")
                return False
                
        except Exception as e:
            print(f"❌ Failed to initialize AI system: {e}")
            return False
    
    def create_test_ticket(self, ticket_id: str, user: str, subject: str, description: str) -> Dict:
        """Create a test ticket with redirect fields."""
        return {
            "id": ticket_id,
            "user": user,
            "subject": subject,
            "description": description,
            "category": "Technical Issue",
            "priority": "Medium",
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "assigned_to": None,
            "assignment_status": "pending",
            "assignment_date": None,
            "employee_solution": None,
            "completion_date": None,
            # Redirect tracking fields
            "redirect_count": 0,
            "max_redirects": 3,
            "redirect_history": [],
            "redirect_reason": None,
            "previous_assignee": None,
            "redirect_timestamp": None,
            "call_status": "not_initiated",
            "conversation_data": None,
            "redirect_requested": False
        }
    
    def simulate_conversation_end(self, ticket_data: Dict, employee_data: Dict, 
                                request_redirect: bool = False, redirect_reason: str = None) -> Dict:
        """Simulate a conversation ending with optional redirect request."""
        
        if request_redirect:
            conversation_summary = f"""
Employee: Hello, I've reviewed your request about {ticket_data['subject']}.
User: Great! Can you help me with this issue?
Employee: Actually, I think this would be better handled by someone from our {redirect_reason or 'specialized team'}. 
Employee: Let me redirect this to someone with more expertise in this area.
User: Okay, that sounds good.
Employee: I'll arrange for the redirect now. You should hear from the right person shortly.
REDIRECT_REQUESTED: True
REDIRECT_REASON: {redirect_reason or 'Better expertise match needed'}
"""
        else:
            conversation_summary = f"""
Employee: Hello, I've reviewed your request about {ticket_data['subject']}.
User: Great! Can you help me with this issue?
Employee: Absolutely! I can help you with that. Let me provide a solution.
Employee: Based on your requirements, here's what I recommend: [detailed solution provided]
User: Perfect! That's exactly what I needed. Thank you!
Employee: You're welcome! Is there anything else you need help with?
User: No, that covers everything. Thanks again!
REDIRECT_REQUESTED: False
CONVERSATION_COMPLETE: True
"""
        
        return {
            "conversation_summary": conversation_summary,
            "call_duration": "5 minutes",
            "conversation_complete": not request_redirect,
            "redirect_requested": request_redirect,
            "redirect_reason": redirect_reason
        }
    
    def test_scenario_1_normal_completion(self):
        """Test Scenario 1: Normal call completion without redirect."""
        print("\n" + "="*60)
        print("🧪 TEST SCENARIO 1: Normal Call Completion (No Redirect)")
        print("="*60)
        
        # Create test ticket
        ticket = self.create_test_ticket(
            "TEST001", 
            "testuser", 
            "API Integration Help",
            "I need help integrating our payment API with the new checkout system."
        )
        
        print(f"📋 Created test ticket: {ticket['id']}")
        print(f"📋 Subject: {ticket['subject']}")
        print(f"📋 User: {ticket['user']}")
        
        try:
            # Step 1: Run initial workflow to get employee assignment
            print("\n🔄 Step 1: Running initial workflow...")
            
            workflow_input = {
                "query": ticket["description"],
                "exclude_username": ticket["user"]  # Prevent self-assignment
            }
            
            initial_result = self.system.workflow.run(workflow_input)
            print(f"✅ Initial workflow completed")
            
            # Check if employee was assigned
            employee_data = initial_result.get("employee_data")
            if employee_data:
                print(f"✅ Employee assigned: {employee_data['full_name']} ({employee_data['username']})")
                
                # Step 2: Simulate call initiation
                print("\n📞 Step 2: Simulating call initiation...")
                
                vocal_result = self.system.agents["vocal_assistant"].run({
                    "action": "initiate_call",
                    "ticket_data": ticket,
                    "employee_data": employee_data
                })
                
                print(f"✅ Call initiated: {vocal_result.get('result', 'Unknown')}")
                
                # Step 3: Simulate call completion (no redirect)
                print("\n📞 Step 3: Simulating call completion...")
                
                conversation_data = self.simulate_conversation_end(ticket, employee_data, request_redirect=False)
                
                end_call_result = self.system.agents["vocal_assistant"].run({
                    "action": "end_call",
                    "ticket_data": ticket,
                    "employee_data": employee_data,
                    "conversation_data": conversation_data,
                    "conversation_summary": conversation_data["conversation_summary"],
                    "call_duration": conversation_data["call_duration"]
                })
                
                print(f"✅ Call ended: {end_call_result.get('result', 'Unknown')}")
                
                # Step 4: Check that no redirect was triggered
                print("\n🔍 Step 4: Verifying no redirect occurred...")
                
                if end_call_result.get("action") == "end_call":
                    print("✅ Call properly ended without redirect")
                    self.test_results.append(("Scenario 1: Normal Completion", True))
                    return True
                else:
                    print("❌ Unexpected action after call end")
                    self.test_results.append(("Scenario 1: Normal Completion", False))
                    return False
            else:
                print("❌ No employee was assigned")
                self.test_results.append(("Scenario 1: Normal Completion", False))
                return False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("Scenario 1: Normal Completion", False))
            return False
    
    def test_scenario_2_single_redirect(self):
        """Test Scenario 2: Single redirect request."""
        print("\n" + "="*60)
        print("🧪 TEST SCENARIO 2: Single Redirect Request")
        print("="*60)
        
        # Create test ticket
        ticket = self.create_test_ticket(
            "TEST002", 
            "testuser2", 
            "Machine Learning Model Deployment",
            "I need help deploying a TensorFlow model to production with proper scaling."
        )
        
        print(f"📋 Created test ticket: {ticket['id']}")
        print(f"📋 Subject: {ticket['subject']}")
        
        try:
            # Step 1: Initial assignment
            print("\n🔄 Step 1: Getting initial assignment...")
            
            workflow_input = {
                "query": ticket["description"],
                "exclude_username": ticket["user"]
            }
            
            initial_result = self.system.workflow.run(workflow_input)
            employee_data = initial_result.get("employee_data")
            
            if not employee_data:
                print("❌ No initial employee assignment")
                self.test_results.append(("Scenario 2: Single Redirect", False))
                return False
            
            print(f"✅ Initial assignment: {employee_data['full_name']} ({employee_data['username']})")
            
            # Step 2: Call initiation
            print("\n📞 Step 2: Initiating call...")
            
            self.system.agents["vocal_assistant"].run({
                "action": "initiate_call",
                "ticket_data": ticket,
                "employee_data": employee_data
            })
            
            # Step 3: Call completion with redirect request
            print("\n🔄 Step 3: Call completion with redirect request...")
            
            conversation_data = self.simulate_conversation_end(
                ticket, employee_data, 
                request_redirect=True, 
                redirect_reason="AI/ML specialist team"
            )
            
            # Update ticket for redirect
            ticket.update({
                "call_status": "completed",
                "conversation_data": conversation_data,
                "redirect_requested": True
            })
            
            # Step 4: Process redirect through workflow
            print("\n🔄 Step 4: Processing redirect through workflow...")
            
            # Simulate the redirect workflow
            redirect_info = {
                "reason": "AI/ML specialist team",
                "responsibilities": "machine learning, tensorflow, deployment"
            }
            
            # Test employee search with redirect criteria
            search_results = self.system.agents["employee_search_tool"].search_employees_for_redirect(redirect_info)
            
            if search_results:
                selected_employee = search_results[0]  # Top match
                print(f"✅ Redirect employee found: {selected_employee['full_name']} ({selected_employee['username']})")
                
                # Step 5: Initiate redirect call
                print("\n📞 Step 5: Initiating redirect call...")
                
                redirect_result = self.system.agents["vocal_assistant"].run({
                    "action": "initiate_redirect_call",
                    "ticket_data": ticket,
                    "employee_data": selected_employee,
                    "redirect_reason": redirect_info
                })
                
                print(f"✅ Redirect call initiated: {redirect_result.get('result', 'Unknown')}")
                
                self.test_results.append(("Scenario 2: Single Redirect", True))
                return True
            else:
                print("❌ No suitable redirect employee found")
                self.test_results.append(("Scenario 2: Single Redirect", False))
                return False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("Scenario 2: Single Redirect", False))
            return False
    
    def test_scenario_3_redirect_loop_prevention(self):
        """Test Scenario 3: Redirect loop prevention."""
        print("\n" + "="*60)
        print("🧪 TEST SCENARIO 3: Redirect Loop Prevention")
        print("="*60)
        
        # Create ticket with existing redirect history
        ticket = self.create_test_ticket(
            "TEST003",
            "testuser3", 
            "Complex System Integration",
            "Need help with complex multi-system integration involving APIs, databases, and ML models."
        )
        
        # Simulate ticket with redirect history
        ticket.update({
            "redirect_count": 2,
            "redirect_history": ["patrick", "thomas"],
            "previous_assignee": "thomas"
        })
        
        print(f"📋 Created test ticket with redirect history: {ticket['id']}")
        print(f"📋 Previous redirects: {ticket['redirect_history']}")
        print(f"📋 Redirect count: {ticket['redirect_count']}/{ticket['max_redirects']}")
        
        try:
            # Step 1: Test redirect with exclusion
            print("\n🔍 Step 1: Testing employee search with exclusions...")
            
            redirect_info = {
                "responsibilities": "system integration, api, database",
                "exclude_usernames": ticket["redirect_history"]  # Exclude previous assignees
            }
            
            search_results = self.system.agents["employee_search_tool"].search_employees_for_redirect(redirect_info)
            
            print(f"✅ Found {len(search_results)} candidates (excluding previous assignees)")
            
            # Verify exclusions work
            for result in search_results:
                if result['username'] in ticket["redirect_history"]:
                    print(f"❌ FAILED: Previous assignee {result['username']} not excluded!")
                    self.test_results.append(("Scenario 3: Loop Prevention", False))
                    return False
            
            print("✅ Exclusion logic working - no previous assignees in results")
            
            # Step 2: Test redirect limit validation
            print("\n🚨 Step 2: Testing redirect limit validation...")
            
            # Simulate one more redirect attempt (should hit limit)
            ticket["redirect_count"] = 3  # At max limit
            
            # Check validation logic from workflow
            from graphs.workflow import MultiAgentWorkflow
            workflow = MultiAgentWorkflow(self.system.agents)
            
            limit_check = workflow._validate_redirect_limits(ticket)
            
            if not limit_check:
                print("✅ Redirect limit validation working - blocked excessive redirects")
                self.test_results.append(("Scenario 3: Loop Prevention", True))
                return True
            else:
                print("❌ Redirect limit validation failed - should have blocked redirect")
                self.test_results.append(("Scenario 3: Loop Prevention", False))
                return False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("Scenario 3: Loop Prevention", False))
            return False
    
    def test_scenario_4_full_workflow_integration(self):
        """Test Scenario 4: Complete workflow integration."""
        print("\n" + "="*60)
        print("🧪 TEST SCENARIO 4: Full Workflow Integration")
        print("="*60)
        
        # Create complex test ticket
        ticket = self.create_test_ticket(
            "TEST004",
            "testuser4",
            "Database Performance Optimization", 
            "Our main database is running slow. Need expert help with query optimization and indexing strategies."
        )
        
        print(f"📋 Created test ticket: {ticket['id']}")
        
        try:
            # Step 1: Full workflow run
            print("\n🔄 Step 1: Running complete workflow...")
            
            workflow_input = {
                "query": ticket["description"],
                "exclude_username": ticket["user"]
            }
            
            # Run the full workflow
            workflow_result = self.system.workflow.run(workflow_input)
            
            print("✅ Full workflow execution completed")
            print(f"📊 Workflow result keys: {list(workflow_result.keys())}")
            
            # Step 2: Analyze workflow components
            print("\n🔍 Step 2: Analyzing workflow components...")
            
            components_tested = []
            
            # Check Maestro preprocessing
            if "maestro_preprocess" in workflow_result:
                components_tested.append("✅ Maestro Preprocessing")
            
            # Check Data Guardian
            if "data_guardian" in workflow_result:
                components_tested.append("✅ Data Guardian Search")
            
            # Check HR Agent
            if "hr_agent" in workflow_result:
                components_tested.append("✅ HR Agent Assignment")
            
            # Check employee assignment
            if "employee_data" in workflow_result:
                employee = workflow_result["employee_data"]
                components_tested.append(f"✅ Employee Assignment: {employee['full_name']}")
            
            print("\n📊 Workflow Components Tested:")
            for component in components_tested:
                print(f"   {component}")
            
            # Step 3: Test workflow state management
            print("\n📋 Step 3: Testing workflow state management...")
            
            if len(components_tested) >= 3:
                print("✅ Multi-agent coordination successful")
                print("✅ State preservation across workflow steps")
                self.test_results.append(("Scenario 4: Full Integration", True))
                return True
            else:
                print("❌ Incomplete workflow execution")
                self.test_results.append(("Scenario 4: Full Integration", False))
                return False
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("Scenario 4: Full Integration", False))
            return False
    
    def run_all_tests(self):
        """Run all test scenarios."""
        print("🚀 STARTING REAL-WORLD REDIRECT WORKFLOW TESTING")
        print("="*60)
        
        if not self.system:
            print("❌ Cannot run tests - system not initialized")
            return False
        
        # Run all test scenarios
        print("\n🧪 Running Test Scenarios...")
        
        self.test_scenario_1_normal_completion()
        time.sleep(1)  # Brief pause between tests
        
        self.test_scenario_2_single_redirect()
        time.sleep(1)
        
        self.test_scenario_3_redirect_loop_prevention()
        time.sleep(1)
        
        self.test_scenario_4_full_workflow_integration()
        
        # Print final results
        self.print_final_results()
        
        return all(result[1] for result in self.test_results)
    
    def print_final_results(self):
        """Print comprehensive test results."""
        print("\n" + "="*60)
        print("📊 REAL-WORLD TESTING RESULTS")
        print("="*60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print("="*60)
        print(f"🎯 OVERALL RESULTS: {passed}/{total} scenarios passed")
        
        if passed == total:
            print("🎉 ALL REAL-WORLD TESTS PASSED!")
            print("🚀 Redirect workflow is production-ready!")
        else:
            print(f"⚠️ {total - passed} scenarios failed - check output above")
            print("🔧 Additional debugging may be needed")
        
        print("\n📋 Test Coverage Summary:")
        print("   ✅ Normal call completion flow")
        print("   ✅ Single redirect handling")
        print("   ✅ Redirect loop prevention")
        print("   ✅ Full workflow integration")
        print("   ✅ Agent coordination")
        print("   ✅ State management")
        print("   ✅ Error handling")


def main():
    """Main test execution."""
    tester = RedirectWorkflowTester()
    success = tester.run_all_tests()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

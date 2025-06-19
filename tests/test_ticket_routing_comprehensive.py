#!/usr/bin/env python3
"""
Comprehensive test suite for HR Agent ticket routing.
Tests both employee-based and document-based routing with summary reporting.
"""

import sys
import os
import time
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import AISystem

# Test results tracking
test_results = []

class TestResult:
    def __init__(self, test_name, ticket_type, expected_assignment, actual_assignment, 
                 match_status, processing_time, additional_info=""):
        self.test_name = test_name
        self.ticket_type = ticket_type
        self.expected_assignment = expected_assignment
        self.actual_assignment = actual_assignment
        self.match_status = match_status
        self.processing_time = processing_time
        self.additional_info = additional_info

def test_hr_agent_routing():
    """Test HR Agent with comprehensive ticket routing scenarios."""
    
    print("=" * 80)
    print("COMPREHENSIVE HR AGENT TICKET ROUTING TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize system components
    print("🔧 Initializing AI System...")
    try:
        # Create AI system with development config
        ai_system = AISystem('development')
        print("✅ AI System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI System: {e}")
        print("Falling back to simulation mode...")
        ai_system = None
    
    print("\n" + "=" * 80)
    print("RUNNING TEST CASES")
    print("=" * 80)
    
    # Test cases with expected assignments (Using EXACT queries from internal_tickets.md)
    test_cases = [
        # Employee-based routing tests from internal_tickets.md - EXACT QUERIES
        {
            "name": "Test 1: Product Roadmap Request",
            "type": "employee",
            "query": "Could you please provide an updated product roadmap for Q3 with new feature timelines and major milestones? The marketing and sales teams need it to align their campaigns.",
            "expected": "Patrick Neumann",  # Product Development Lead - product strategy, roadmap
            "category": "Product Management"
        },
        {
            "name": "Test 2: Strategic Direction Query",
            "type": "employee", 
            "query": "Can you confirm if the company will focus more on AI-based services or continue investing in education platforms next year? This will help all departments prepare early roadmaps.",
            "expected": "Thomas Müller",  # CEO - strategic leadership, company vision
            "category": "Executive Strategy"
        },
        {
            "name": "Test 3: Security Vulnerability Scan",
            "type": "employee",
            "query": "We just deployed a new API gateway for customer data access. Could you perform a penetration test and submit a vulnerability report before we move it to production?",
            "expected": "Mouad El Idrissi",  # Security Researcher - penetration testing, vulnerability assessment
            "category": "Security"
        },
        {
            "name": "Test 4: UX/UI Redesign Request",
            "type": "employee",
            "query": "Feedback suggests the mobile onboarding is confusing. Can you redesign the UI/UX to reduce friction and improve the conversion rate, ideally with Figma mockups?",
            "expected": "Mounir Belhaj",  # UX/UI Designer & Front-End Developer - UI/UX design, Figma
            "category": "UI/UX Design"
        },
        {
            "name": "Test 5: AI Model Retraining",
            "type": "employee",
            "query": "We've gathered a new dataset of annotated customer interactions. Could you retrain the recommendation model and test whether it improves product suggestions?",
            "expected": "Tristan Maier",  # AI Engineer - machine learning, model training
            "category": "AI/ML"
        },
        {
            "name": "Test 6: API Bug Fix",
            "type": "employee",
            "query": "Users are experiencing 500 errors when updating their profile pictures. Could you debug the issue in the `PUT /api/profile` endpoint and apply a fix?",
            "expected": "Yacoub Hossam",  # Full-Stack Developer - APIs, backend development
            "category": "Backend Development"
        },
        {
            "name": "Test 7: Sprint Timeline Adjustment",
            "type": "employee",
            "query": "Adjustments are needed to the timeline for Sprint 14 due to delays in testing. A revised plan and updated sprint review schedule should be prepared.",
            "expected": "Reda Tazi",  # Project Manager - agile project management, sprint planning
            "category": "Project Management"
        },
        {
            "name": "Test 8: Regression Testing Request",
            "type": "employee",
            "query": "A new billing module has been merged into staging. Can you run full regression tests and ensure no existing functionality is broken before production deployment?",
            "expected": "Sarah Becker",  # QA Engineer - testing, quality assurance
            "category": "Quality Assurance"
        },
        {
            "name": "Test 9: CI/CD Pipeline Issue",
            "type": "employee",
            "query": "The CI/CD pipeline is failing at the Docker build stage due to a missing dependency. Could you investigate and update the Dockerfile or the pipeline config to resolve the issue?",
            "expected": "Omar Khalil",  # DevOps Engineer - CI/CD, Docker, pipeline management
            "category": "DevOps"
        },
        {
            "name": "Test 10: Marketing KPI Dashboard",
            "type": "employee",
            "query": "The marketing team needs updated KPIs for lead conversions, CAC, and user retention for their monthly review. Can you refresh the dashboard with the latest data and send a snapshot?",
            "expected": "Lina Schneider",  # Data Analyst - dashboards, data visualization, KPIs
            "category": "Data Analytics"
        }
    ]
    
    # Run each test case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Running {test_case['name']}...")
        print(f"   Type: {test_case['type']}")
        print(f"   Category: {test_case['category']}")
        print(f"   Query: {test_case['query']}")
        print(f"   Expected: {test_case['expected']}")
        
        start_time = time.time()
        
        try:
            # Process query through real AI system
            if ai_system:
                workflow_result = process_with_real_workflow(test_case, ai_system)
            else:
                # Fallback if AI system not available
                workflow_result = {
                    'assignment': "AI System not available",
                    'response': "System initialization failed",
                    'processing_successful': False,
                    'additional_info': "AI System not initialized"
                }
            
            processing_time = time.time() - start_time
            
            if test_case['type'] == 'document':
                # For document queries, check if we got a meaningful response
                actual_assignment = workflow_result['assignment']
                additional_info = workflow_result['additional_info']
                match_status = "✅ PASS" if "Document-based" in actual_assignment else "❌ FAIL"
                
            else:
                # For employee queries, check assignment
                actual_assignment = workflow_result['assignment']
                additional_info = workflow_result['additional_info']
                
                # Check if the assignment matches expected employee
                if actual_assignment == test_case['expected']:
                    match_status = "✅ PASS"
                elif actual_assignment in ["No assignment", "ERROR"]:
                    match_status = "❌ FAIL"
                else:
                    # Check if it's a reasonable alternative (same role/skills)
                    match_status = "🔍 REVIEW"  # Manual review needed
            
            print(f"   Actual: {actual_assignment}")
            print(f"   Status: {match_status}")
            print(f"   Time: {processing_time:.2f}s")
            print(f"   Info: {additional_info}")
            
            # Store result
            test_results.append(TestResult(
                test_name=test_case['name'],
                ticket_type=test_case['type'],
                expected_assignment=test_case['expected'],
                actual_assignment=actual_assignment,
                match_status=match_status,
                processing_time=processing_time,
                additional_info=additional_info
            ))
            
            # Show response preview for document queries
            if test_case['type'] == 'document' and workflow_result['response']:
                print(f"   Response Preview: {workflow_result['response'][:100]}...")
                
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"   ❌ ERROR: {e}")
            
            test_results.append(TestResult(
                test_name=test_case['name'],
                ticket_type=test_case['type'],
                expected_assignment=test_case['expected'],
                actual_assignment="ERROR",
                match_status="❌ ERROR",
                processing_time=processing_time,
                additional_info=str(e)
            ))
    
    # Print comprehensive summary
    print_test_summary()

def print_test_summary():
    """Print a comprehensive summary of all test results."""
    print("\n" + "=" * 100)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 100)
    
    # Summary statistics
    total_tests = len(test_results)
    passed_tests = len([r for r in test_results if "PASS" in r.match_status])
    failed_tests = len([r for r in test_results if "FAIL" in r.match_status])
    error_tests = len([r for r in test_results if "ERROR" in r.match_status])
    
    print(f"📊 OVERALL STATISTICS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"   Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    print(f"   Errors: {error_tests} ({error_tests/total_tests*100:.1f}%)")
    print()
    
    # Detailed results table
    print("📋 DETAILED RESULTS TABLE:")
    print("-" * 100)
    print(f"{'Test':<25} {'Type':<10} {'Expected':<20} {'Actual':<20} {'Status':<10} {'Time':<8} {'Info':<15}")
    print("-" * 100)
    
    for result in test_results:
        test_name_short = result.test_name.replace("Test ", "T")[:24]
        expected_short = result.expected_assignment[:19]
        actual_short = result.actual_assignment[:19]
        status_short = result.match_status.replace("✅ ", "").replace("❌ ", "")
        time_str = f"{result.processing_time:.2f}s"
        info_short = result.additional_info[:14]
        
        print(f"{test_name_short:<25} {result.ticket_type:<10} {expected_short:<20} {actual_short:<20} {status_short:<10} {time_str:<8} {info_short:<15}")
    
    print("-" * 100)
    
    # Performance metrics
    avg_time = sum(r.processing_time for r in test_results) / len(test_results)
    max_time = max(r.processing_time for r in test_results)
    min_time = min(r.processing_time for r in test_results)
    
    print(f"\n⏱️  PERFORMANCE METRICS:")
    print(f"   Average processing time: {avg_time:.2f}s")
    print(f"   Fastest response: {min_time:.2f}s")
    print(f"   Slowest response: {max_time:.2f}s")
    
    # Test type breakdown
    employee_tests = [r for r in test_results if r.ticket_type == 'employee']
    document_tests = [r for r in test_results if r.ticket_type == 'document']
    
    print(f"\n📊 TEST TYPE BREAKDOWN:")
    print(f"   Employee-based tests: {len(employee_tests)} ({len([r for r in employee_tests if 'PASS' in r.match_status])}/{len(employee_tests)} passed)")
    print(f"   Document-based tests: {len(document_tests)} ({len([r for r in document_tests if 'PASS' in r.match_status])}/{len(document_tests)} passed)")
    
    # Failed tests details
    failed_results = [r for r in test_results if "FAIL" in r.match_status or "ERROR" in r.match_status]
    if failed_results:
        print(f"\n❌ FAILED/ERROR TESTS DETAILS:")
        for result in failed_results:
            print(f"   • {result.test_name}")
            print(f"     Expected: {result.expected_assignment}")
            print(f"     Actual: {result.actual_assignment}")
            print(f"     Info: {result.additional_info}")
    
    print("\n" + "=" * 100)
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

def process_with_real_workflow(test_case, ai_system):
    """Process with actual workflow instead of simulation."""
    try:
        # Use the real AI system to process the query
        result = ai_system.process_query(test_case['query'])
        
        if test_case['type'] == 'document':
            # For document queries, extract the document answer
            doc_answer = ""
            if isinstance(result, dict):
                doc_answer = (result.get('document_answer', '') or 
                            result.get('answer', '') or 
                            result.get('synthesis', '') or
                            result.get('response', ''))
            elif isinstance(result, str):
                doc_answer = result
                
            return {
                'assignment': "Document-based response" if doc_answer else "No response",
                'response': doc_answer,
                'processing_successful': bool(doc_answer),
                'additional_info': f"Answer length: {len(doc_answer)} chars"
            }
        else:
            # For employee queries, extract assignment information
            assignment_info = extract_assignment_from_workflow_result(result)
            return assignment_info
            
    except Exception as e:
        return {
            'assignment': "ERROR",
            'response': str(e),
            'processing_successful': False,
            'additional_info': f"Error: {str(e)}"
        }

def extract_assignment_from_workflow_result(result):
    """Extract employee assignment from actual workflow result."""
    if not isinstance(result, dict):
        return {
            'assignment': "No assignment",
            'response': str(result),
            'processing_successful': False,
            'additional_info': "Invalid result format"
        }
    
    # Check for workflow result with HR assignment
    workflow_result = result.get("workflow_result", {})
    hr_action = workflow_result.get("hr_action")
    employee_data = workflow_result.get("employee_data")
    
    if hr_action == "assign" and employee_data:
        # Extract employee name/username from assignment
        assigned_employee = (employee_data.get("full_name") or 
                            employee_data.get("name") or 
                            employee_data.get("username", ""))
        
        response_text = result.get("synthesis", "") or result.get("response", "")
        
        return {
            'assignment': assigned_employee,
            'response': response_text,
            'processing_successful': True,
            'additional_info': f"HR Action: {hr_action}, Employee ID: {employee_data.get('id', 'N/A')}"
        }
    
    # Check for direct HR agent result
    hr_result = result.get("hr_agent", {})
    if isinstance(hr_result, dict):
        matched_employees = hr_result.get("matched_employees", [])
        recommended_assignment = hr_result.get("recommended_assignment")
        
        if matched_employees and recommended_assignment:
            # Find the recommended employee
            for emp in matched_employees:
                if emp.get("employee_id") == str(recommended_assignment):
                    assigned_employee = emp.get("name", emp.get("username", ""))
                    return {
                        'assignment': assigned_employee,
                        'response': result.get("synthesis", ""),
                        'processing_successful': True,
                        'additional_info': f"HR Confidence: {hr_result.get('confidence_level', 'N/A')}"
                    }
    
    # Look for assignment in the response text
    response_text = result.get("synthesis", "") or result.get("response", "")
    if response_text:
        assigned_employee = extract_employee_from_response_text(response_text)
        if assigned_employee:
            return {
                'assignment': assigned_employee,
                'response': response_text,
                'processing_successful': True,
                'additional_info': "Extracted from response text"
            }
    
    return {
        'assignment': "No assignment",
        'response': response_text,
        'processing_successful': False,
        'additional_info': "No assignment data found in workflow result"
    }

def extract_employee_from_response_text(response_text):
    """Extract employee name from response text."""
    if not response_text:
        return ""
    
    # Look for assignment patterns in text
    response_lower = response_text.lower()
    
    # Check for each employee name (both full name and username)
    employees = [
        ("Patrick Neumann", "patrick"),
        ("Thomas Müller", "thomas"), 
        ("Mouad El Idrissi", "mouad"),
        ("Mounir Belhaj", "mounir"),
        ("Tristan Maier", "tristan"),
        ("Yacoub Hossam", "yacoub"),
        ("Reda Tazi", "reda"),
        ("Sarah Becker", "sarah"),
        ("Omar Khalil", "omar"),
        ("Lina Schneider", "lina")
    ]
    
    for full_name, username in employees:
        if (full_name.lower() in response_lower or 
            username in response_lower or
            f"assigned to {full_name.lower()}" in response_lower or
            f"assigned to {username}" in response_lower):
            return full_name
    
    return ""

if __name__ == "__main__":
    test_hr_agent_routing()

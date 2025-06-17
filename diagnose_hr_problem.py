#!/usr/bin/env python3
"""
Diagnostic script to investigate the HR_Agent assignment problem.
This script will analyze why ML questions are going to Product Manager instead of ML experts.
"""

import sys
import os
sys.path.append('src')
sys.path.append('front')

# Mock streamlit session state
class MockSessionState:
    def __init__(self):
        self.username = "mounir"

class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()

# Mock streamlit
sys.modules['streamlit'] = MockStreamlit()

from front.database import db_manager
from src.tools.availability_tool import AvailabilityTool
from src.agents.base_agent import HRAgent


def analyze_employee_database():
    """Analyze the employee database to understand availability and expertise."""
    print("🔍 ANALYZING EMPLOYEE DATABASE")
    print("=" * 50)
    
    all_employees = db_manager.get_all_employees()
    
    print(f"📊 Total employees: {len(all_employees)}")
    print("\n👥 Employee Details:")
    
    for emp in all_employees:
        status = emp.get('availability_status', 'NOT SET')
        print(f"\n🔸 {emp['full_name']} (@{emp['username']})")
        print(f"   Role: {emp['role_in_company']}")
        print(f"   Expertise: {emp['expertise']}")
        print(f"   Responsibilities: {emp['responsibilities']}")
        print(f"   Status: {status}")
        print(f"   Active: {emp.get('is_active', 'NOT SET')}")
    
    # Analyze status distribution
    status_counts = {}
    ml_experts = []
    
    for emp in all_employees:
        status = emp.get('availability_status', 'Offline')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # Identify ML experts
        expertise = emp.get('expertise', '').lower()
        role = emp.get('role_in_company', '').lower()
        if any(keyword in expertise + role for keyword in ['machine learning', 'data scientist', 'ml', 'deep learning']):
            ml_experts.append(emp)
    
    print(f"\n📈 Status Distribution:")
    for status, count in status_counts.items():
        print(f"   {status}: {count} employees")
    
    print(f"\n🤖 ML Experts Found:")
    for expert in ml_experts:
        print(f"   • {expert['full_name']} (@{expert['username']}) - {expert['availability_status']}")
    
    return all_employees, ml_experts


def analyze_availability_tool_filtering():
    """Analyze how AvailabilityTool filters employees."""
    print("\n🔧 ANALYZING AVAILABILITY TOOL FILTERING")
    print("=" * 55)
    
    availability_tool = AvailabilityTool()
    available_employees = availability_tool.get_available_employees()
    
    print(f"📋 Available employees: {len(available_employees['available'])}")
    print(f"📋 Busy employees: {len(available_employees['busy'])}")
    print(f"📋 Total online: {available_employees['total_online']}")
    
    all_candidates = available_employees['available'] + available_employees['busy']
    print(f"\n👥 All candidates after filtering (excluding mounir):")
    
    for emp in all_candidates:
        print(f"   • {emp['full_name']} (@{emp['username']}) - {emp['role_in_company']} - {emp['availability_status']}")
    
    return available_employees


def analyze_hr_agent_scoring():
    """Analyze HR_Agent scoring algorithm with the test query."""
    print("\n🤖 ANALYZING HR_AGENT SCORING")
    print("=" * 40)
    
    test_query = "which model is should i use for a classification problem?"
    print(f"📝 Test Query: {test_query}")
    
    # Get candidates
    availability_tool = AvailabilityTool()
    available_employees = availability_tool.get_available_employees()
    candidates = available_employees["available"] + available_employees["busy"]
    
    if not candidates:
        print("❌ No candidates available!")
        return
    
    # Simulate HR_Agent scoring
    query_lower = test_query.lower()
    query_words = query_lower.split()
    
    print(f"\n🔍 Query words: {query_words}")
    print(f"\n📊 Scoring Analysis:")
    
    scored_candidates = []
    for employee in candidates:
        score = 0
        role = employee.get('role_in_company', '').lower()
        expertise = employee.get('expertise', '').lower()
        responsibilities = employee.get('responsibilities', '').lower()
        
        print(f"\n🔸 {employee['full_name']} (@{employee['username']}):")
        print(f"   Role: {role}")
        print(f"   Expertise: {expertise}")
        print(f"   Responsibilities: {responsibilities}")
        
        role_matches = []
        expertise_matches = []
        responsibility_matches = []
        
        # Score based on keyword matches
        for keyword in query_words:
            if keyword in role:
                score += 3
                role_matches.append(keyword)
            if keyword in expertise:
                score += 5
                expertise_matches.append(keyword)
            if keyword in responsibilities:
                score += 2
                responsibility_matches.append(keyword)
        
        # Prefer available over busy
        availability_bonus = 0
        if employee.get('availability_status') == 'Available':
            score += 1
            availability_bonus = 1
        
        print(f"   Role matches: {role_matches} (+{len(role_matches) * 3})")
        print(f"   Expertise matches: {expertise_matches} (+{len(expertise_matches) * 5})")
        print(f"   Responsibility matches: {responsibility_matches} (+{len(responsibility_matches) * 2})")
        print(f"   Availability bonus: +{availability_bonus}")
        print(f"   TOTAL SCORE: {score}")
        
        scored_candidates.append((score, employee))
    
    # Sort by score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n🏆 FINAL RANKING:")
    for i, (score, emp) in enumerate(scored_candidates, 1):
        status_emoji = "🟢" if emp.get('availability_status') == 'Available' else "🟡"
        print(f"   {i}. {emp['full_name']} (@{emp['username']}) - Score: {score} {status_emoji}")
    
    if scored_candidates:
        winner = scored_candidates[0][1]
        print(f"\n🎯 WOULD BE ASSIGNED TO: {winner['full_name']} (@{winner['username']})")
    
    return scored_candidates


def test_actual_hr_agent():
    """Test the actual HR_Agent to see what it returns."""
    print("\n🎭 TESTING ACTUAL HR_AGENT")
    print("=" * 35)
    
    availability_tool = AvailabilityTool()
    hr_agent = HRAgent(availability_tool=availability_tool)
    
    test_query = "which model is should i use for a classification problem?"
    result = hr_agent.run({"query": test_query})
    
    print(f"📝 Query: {test_query}")
    print(f"📊 HR_Agent Result:")
    print(f"   Status: {result.get('status')}")
    print(f"   Action: {result.get('action')}")
    
    if result.get('employee_data'):
        emp = result.get('employee_data')
        print(f"   Assigned: {emp.get('full_name')} (@{emp.get('username')})")
        print(f"   Role: {emp.get('role_in_company')}")
        print(f"   Expertise: {emp.get('expertise')}")
    
    print(f"   Response: {result.get('result', '')[:200]}...")
    
    return result


def main():
    """Run complete diagnostic analysis."""
    print("🚀 HR_AGENT ASSIGNMENT PROBLEM DIAGNOSTIC")
    print("=" * 70)
    
    try:
        # Step 1: Analyze employee database
        all_employees, ml_experts = analyze_employee_database()
        
        # Step 2: Analyze availability filtering
        available_employees = analyze_availability_tool_filtering()
        
        # Step 3: Analyze scoring algorithm
        scored_candidates = analyze_hr_agent_scoring()
        
        # Step 4: Test actual HR_Agent
        hr_result = test_actual_hr_agent()
        
        # Step 5: Summary and diagnosis
        print(f"\n💡 PROBLEM DIAGNOSIS SUMMARY")
        print("=" * 40)
        
        # Check if ML experts are available
        ml_available = any(emp['username'] in ['alex01', 'yacoub'] 
                          for emp in available_employees['available'] + available_employees['busy'])
        
        print(f"🔍 ML Experts Available: {'Yes' if ml_available else 'No'}")
        
        if not ml_available:
            print("❌ PROBLEM FOUND: No ML experts are Available/Busy status")
            print("   Solution: Set Alex Johnson and/or Yacoub to 'Available' status")
        
        # Check keyword matching
        if scored_candidates:
            top_score = scored_candidates[0][0]
            top_employee = scored_candidates[0][1]
            
            if top_score == 0:
                print("❌ PROBLEM FOUND: No keyword matches found")
                print("   Solution: Improve keyword matching for ML terms")
            elif 'product manager' in top_employee.get('role_in_company', '').lower():
                print("❌ PROBLEM FOUND: Product Manager scoring higher than ML experts")
                print("   Solution: Check why ML experts have lower scores")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

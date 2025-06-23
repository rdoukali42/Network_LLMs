"""
Employee Search Tool - Searches employees by name, role, or responsibilities for redirection.
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add front directory to path to import database
front_dir = Path(__file__).parent.parent.parent / "front"
sys.path.append(str(front_dir))

from database import db_manager


class EmployeeSearchTool:
    """Tool to search employees by name, role, or responsibilities for ticket redirection."""
    
    def __init__(self):
        self.name = "employee_search"
        self.description = "Search employees by username, role, or responsibilities for redirection"
    
    def search_employees_for_redirect(self, redirect_info: Dict) -> List[Dict]:
        """
        Search for employees matching redirect criteria.
        
        Args:
            redirect_info: Dictionary containing search criteria like:
                - username: specific username to find
                - role: role/title to match
                - responsibilities: expertise/responsibilities to match
                - exclude_usernames: list of usernames to exclude (prevent ping-pong redirects)
        
        Returns:
            List of matching employees with relevance scores
        """
        print(f"   🔍 EmployeeSearchTool: Starting search with criteria: {redirect_info}")
        
        all_employees = db_manager.get_all_employees()
        print(f"   🔍 EmployeeSearchTool: Total employees in database: {len(all_employees)}")
        
        # 🆕 REDIRECT LOOP PREVENTION: Exclude previous assignees
        exclude_usernames = redirect_info.get("exclude_usernames", [])
        if exclude_usernames:
            print(f"   🚫 EmployeeSearchTool: Excluding previous assignees: {exclude_usernames}")
            all_employees = [emp for emp in all_employees if emp.get("username") not in exclude_usernames]
            print(f"   🔍 EmployeeSearchTool: Remaining employees after exclusion: {len(all_employees)}")
        
        matches = []
        
        username = redirect_info.get("username", "").lower()
        role = redirect_info.get("role", "").lower()
        responsibilities = redirect_info.get("responsibilities", "").lower()
        
        print(f"   🔍 EmployeeSearchTool: Search parameters:")
        print(f"      - Username: '{username}'")
        print(f"      - Role: '{role}'")
        print(f"      - Responsibilities: '{responsibilities}'")
        print(f"      - Excluded users: {exclude_usernames}")
        
        for i, emp in enumerate(all_employees):
            score = 0
            reasons = []
            
            print(f"   🔍 EmployeeSearchTool: Evaluating employee {i+1}: {emp.get('full_name', 'Unknown')}")
            
            # Username matching (exact or partial)
            if username:
                emp_username = emp.get("username", "").lower()
                print(f"      - Checking username: '{emp_username}' vs '{username}'")
                if username == emp_username:
                    score += 20  # Exact username match is highest priority
                    reasons.append(f"Exact username match: {username}")
                    print(f"        ✅ Exact username match! Score: +20")
                elif username in emp_username or emp_username in username:
                    score += 15  # Partial username match
                    reasons.append(f"Partial username match: {username}")
                    print(f"        ✅ Partial username match! Score: +15")
            
            # Role matching
            if role:
                emp_role = emp.get("role_in_company", "").lower()
                print(f"      - Checking role: '{emp_role}' vs '{role}'")
                if role in emp_role or emp_role in role:
                    score += 10
                    reasons.append(f"Role match: {role}")
                    print(f"        ✅ Role match! Score: +10")
            
            # Responsibilities/expertise matching
            if responsibilities:
                emp_expertise = emp.get("expertise", "").lower()
                print(f"      - Checking expertise: '{emp_expertise}' vs '{responsibilities}'")
                # Split responsibilities into keywords for better matching
                resp_keywords = [kw.strip() for kw in responsibilities.split(",")]
                
                for keyword in resp_keywords:
                    if keyword and (keyword in emp_expertise or any(keyword in exp.strip() for exp in emp_expertise.split(","))):
                        score += 8
                        reasons.append(f"Expertise match: {keyword}")
                        print(f"        ✅ Expertise match for '{keyword}'! Score: +8")
                        break  # Avoid duplicate scoring for same employee
            
            print(f"      - Final score for {emp.get('full_name', 'Unknown')}: {score}")
            if reasons:
                print(f"      - Match reasons: {reasons}")
            
            # Only include employees with some relevance
            if score > 0:
                matches.append({
                    **emp,
                    "redirect_score": score,
                    "match_reasons": reasons
                })
        
        # Sort by relevance score (highest first)
        matches.sort(key=lambda x: x["redirect_score"], reverse=True)
        
        print(f"   ✅ EmployeeSearchTool: Found {len(matches)} matches")
        for i, match in enumerate(matches):
            print(f"      {i+1}. {match.get('full_name', 'Unknown')} (Score: {match.get('redirect_score', 0)})")
        
        # Return all matches that actually match the criteria
        return matches
    
    def get_employee_by_exact_username(self, username: str) -> Dict:
        """
        Get a specific employee by exact username match.
        
        Args:
            username: Exact username to find
            
        Returns:
            Employee dictionary or empty dict if not found
        """
        all_employees = db_manager.get_all_employees()
        
        for emp in all_employees:
            if emp.get("username", "").lower() == username.lower():
                return emp
        
        return {}


# Create a default instance for easy import
employee_search_tool = EmployeeSearchTool()

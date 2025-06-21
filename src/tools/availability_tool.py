"""
Availability Tool - Checks employee availability status for ticket routing.
"""

from typing import Dict, List
import sys
from pathlib import Path

# Add front directory to path to import database
front_dir = Path(__file__).parent.parent.parent / "front"
sys.path.append(str(front_dir))

from database import db_manager


class AvailabilityTool:
    """Tool to check employee availability status for intelligent ticket routing."""
    
    def __init__(self):
        self.name = "availability_checker"
        self.description = "Check employee availability status for ticket routing"
    
    def get_available_employees(self, exclude_username: str = None) -> Dict:
        """
        Get current employee availability status organized for routing.
        Automatically excludes the current user from session state to prevent self-assignment.
        
        Args:
            exclude_username: Deprecated parameter (kept for backward compatibility)
        
        Returns:
            Dict with employee availability data
        """
        # Auto-cleanup expired statuses first
        db_manager.auto_cleanup_expired_statuses()
        
        # Get all active employees
        all_employees = db_manager.get_all_employees()
        
        # Automatically exclude current user from session state to prevent self-assignment
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'username'):
                current_user = st.session_state.username
                all_employees = [emp for emp in all_employees if emp.get('username') != current_user]
                # print(f"🚫 Automatically excluded current user '{current_user}' from employee list")
        except (ImportError, AttributeError):
            # Fall back to exclude_username parameter if streamlit not available
            if exclude_username:
                all_employees = [emp for emp in all_employees if emp.get('username') != exclude_username]
                print(f"🚫 Excluded user '{exclude_username}' from employee list (fallback mode)")
        
        # Organize by availability status
        availability_data = {
            "available": [],
            "busy": [],
            "total_online": 0,
            "by_expertise": {}
        }
        
        for employee in all_employees:
            status = employee.get('availability_status', 'Offline')
            
            if status == 'Available':
                availability_data["available"].append(employee)
                availability_data["total_online"] += 1
                self._add_to_expertise(availability_data["by_expertise"], employee, "available")
                
            elif status == 'Busy':
                availability_data["busy"].append(employee)
                availability_data["total_online"] += 1
                self._add_to_expertise(availability_data["by_expertise"], employee, "busy")
        
        return availability_data
    
    def _add_to_expertise(self, expertise_dict: Dict, employee: Dict, status: str):
        """Add employee to expertise categorization."""
        expertise = employee.get('expertise', 'General')
        
        if expertise not in expertise_dict:
            expertise_dict[expertise] = {"available": [], "busy": []}
        
        expertise_dict[expertise][status].append(employee)
    
    def get_best_available_for_expertise(self, required_expertise: str) -> List[Dict]:
        """
        Get best available employees for specific expertise.
        
        Args:
            required_expertise: The expertise area needed
            
        Returns:
            List of available employees with matching expertise
        """
        availability_data = self.get_available_employees()
        
        # First try available employees with matching expertise
        for expertise, employees in availability_data["by_expertise"].items():
            if required_expertise.lower() in expertise.lower():
                if employees["available"]:
                    return employees["available"]
        
        # Fallback to any available employees
        return availability_data["available"]
    
    def is_employee_available(self, username: str) -> bool:
        """
        Check if specific employee is available for tickets.
        
        Args:
            username: Employee username to check
            
        Returns:
            True if employee is available, False otherwise
        """
        availability = db_manager.get_employee_availability(username)
        
        if not availability:
            return False
            
        status = availability.get('availability_status', 'Offline')
        return status == 'Available'
    
    def run(self, query: str = "") -> str:
        """
        Tool interface for LangChain integration.
        
        Args:
            query: Optional query parameter
            
        Returns:
            String representation of availability data
        """
        availability_data = self.get_available_employees()
        
        result = f"Employee Availability Status:\n"
        result += f"Total Online: {availability_data['total_online']}\n"
        result += f"Available for tickets: {len(availability_data['available'])}\n"
        result += f"Busy (limited availability): {len(availability_data['busy'])}\n\n"
        
        if availability_data['available']:
            result += "Available Employees:\n"
            for emp in availability_data['available']:
                result += f"- {emp['full_name']} ({emp['role_in_company']}) - {emp['expertise']}\n"
        
        return result


# Tool instance for easy import
availability_tool = AvailabilityTool()

"""
Availability Tool - Checks employee availability status for ticket routing.
Refactored for optimized_project.
"""

from typing import Dict, List, Any, Optional

# DatabaseManager will be injected or imported from the new location
# from data_management.database import DatabaseManager # Example of direct import if needed
# For better testability, DatabaseManager instance should be passed to __init__

class AvailabilityTool:
    """
    Tool to check employee availability status for intelligent ticket routing.
    Requires a DatabaseManager instance for its operations.
    """

    def __init__(self, db_manager_instance: Any, name: str = "availability_checker",
                 description: str = "Check employee availability status for ticket routing"):
        """
        Initializes the AvailabilityTool.
        Args:
            db_manager_instance: An instance of DatabaseManager.
            name: Name of the tool.
            description: Description of the tool.
        """
        self.db_manager = db_manager_instance
        self.name = name
        self.description = description

    def get_available_employees(self, exclude_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current employee availability status organized for routing.

        Args:
            exclude_username: Username of an employee to exclude from the results (e.g., current user).

        Returns:
            Dict with employee availability data:
            {
                "available": List[Dict],
                "busy": List[Dict],
                "total_online": int,
                "by_expertise": Dict[str, Dict[str, List[Dict]]]
            }
        """
        self.db_manager.auto_cleanup_expired_statuses()
        all_employees = self.db_manager.get_all_employees(active_only=True)

        if exclude_username:
            all_employees = [emp for emp in all_employees if emp.get('username') != exclude_username]
            # print(f"🚫 Excluded user '{exclude_username}' from employee list for availability check.")

        availability_data: Dict[str, Any] = {
            "available": [],
            "busy": [],
            "total_online": 0,
            "by_expertise": {}
        }

        for employee in all_employees:
            status = employee.get('availability_status', 'Offline')

            # Consider 'Available' and 'Busy' as online for routing purposes,
            # but differentiate them. 'In Meeting' and 'Do Not Disturb' are treated as busy/unavailable.
            if status == 'Available':
                availability_data["available"].append(employee)
                availability_data["total_online"] += 1
                self._add_to_expertise_map(availability_data["by_expertise"], employee, "available")
            elif status == 'Busy': # Could also include 'In Meeting', 'Do Not Disturb' here if they can still be assigned
                availability_data["busy"].append(employee)
                availability_data["total_online"] += 1
                self._add_to_expertise_map(availability_data["by_expertise"], employee, "busy")
            # Employees with 'Offline', 'In Meeting', 'Do Not Disturb' are not added to 'available' or 'busy' lists directly
            # but 'total_online' reflects those who are not strictly 'Offline'.
            # This logic might need refinement based on exact requirements for "online".
            # For now, total_online counts 'Available' and 'Busy'.

        return availability_data

    def _add_to_expertise_map(self, expertise_map: Dict[str, Dict[str, List[Dict]]],
                              employee: Dict[str, Any], status_key: str):
        """Helper to add employee to the expertise categorization map."""
        # Expertise can be a comma-separated string, split it into a list
        expertise_areas_str = employee.get('expertise', 'General')
        expertise_list = [e.strip() for e in expertise_areas_str.split(',') if e.strip()]
        if not expertise_list: # Default if empty after split
            expertise_list = ['General']

        for expertise_area in expertise_list:
            if expertise_area not in expertise_map:
                expertise_map[expertise_area] = {"available": [], "busy": []}

            # Avoid duplicates if an employee has multiple expertise areas listed
            # and is added multiple times to the same status_key list for that expertise.
            # However, an employee can be in expertise_map[area1][status_key] and expertise_map[area2][status_key].
            # This specific check is for within a single expertise_area's status_key list.
            is_already_added = any(emp['username'] == employee['username'] for emp in expertise_map[expertise_area][status_key])
            if not is_already_added:
                 expertise_map[expertise_area][status_key].append(employee)

    def get_best_available_for_expertise(self, required_expertise: str, exclude_username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get best available employees for a specific expertise.
        Prioritizes 'Available' employees, then 'Busy'.

        Args:
            required_expertise: The expertise area needed.
            exclude_username: Optional username to exclude.

        Returns:
            List of suitable employees (dictionaries).
        """
        availability_data = self.get_available_employees(exclude_username=exclude_username)

        matched_available: List[Dict[str, Any]] = []
        matched_busy: List[Dict[str, Any]] = []

        # Search for matching expertise
        for expertise_area, status_map in availability_data["by_expertise"].items():
            if required_expertise.lower() in expertise_area.lower():
                matched_available.extend(emp for emp in status_map.get("available", []) if emp not in matched_available)
                matched_busy.extend(emp for emp in status_map.get("busy", []) if emp not in matched_busy)

        # Return available first, then busy
        if matched_available:
            return matched_available
        if matched_busy:
            return matched_busy

        # Fallback: if no specific expertise match, return any available employee, then any busy.
        # This part might need more sophisticated scoring in a real system.
        if availability_data["available"]:
            return availability_data["available"]
        if availability_data["busy"]:
            return availability_data["busy"]

        return []

    def is_employee_available_for_assignment(self, username: str) -> bool:
        """
        Check if a specific employee is considered available for new assignments.
        'Available' status means yes.

        Args:
            username: Employee username to check.

        Returns:
            True if employee is 'Available', False otherwise.
        """
        availability_info = self.db_manager.get_employee_availability(username)
        if not availability_info:
            return False
        return availability_info.get('availability_status') == 'Available'

    def run(self, query: str = "", exclude_username: Optional[str] = None) -> str:
        """
        Tool interface for LangChain or direct calls.

        Args:
            query: Optional query parameter (e.g., can contain required expertise).
                   For this version, query is not directly used to parse expertise,
                   use get_best_available_for_expertise for that.
            exclude_username: Username to exclude from results.

        Returns:
            String representation of general availability data.
        """
        # The 'query' param for run is often a string. If it's meant to carry structured info
        # like 'required_expertise' or 'exclude_username', the caller (agent) needs to parse it
        # or call more specific methods like get_best_available_for_expertise.

        availability_data = self.get_available_employees(exclude_username=exclude_username)

        result_str = f"Employee Availability Status:\n"
        result_str += f"  Total Online (Available or Busy): {availability_data['total_online']}\n"
        result_str += f"  Strictly Available: {len(availability_data['available'])}\n"
        result_str += f"  Busy: {len(availability_data['busy'])}\n\n"

        if availability_data['available']:
            result_str += "Available Employees:\n"
            for emp in availability_data['available'][:5]: # Limit output for brevity
                result_str += f"  - {emp.get('full_name', 'N/A')} ({emp.get('role_in_company', 'N/A')}) - Expertise: {emp.get('expertise', 'N/A')}\n"
            if len(availability_data['available']) > 5:
                result_str += "  ... and more.\n"
        else:
            result_str += "No employees are strictly 'Available' right now.\n"

        return result_str.strip()

# Example usage (for testing)
if __name__ == '__main__':
    from pathlib import Path
    # This setup is for standalone testing of this module.
    # In the actual app, DatabaseManager instance would be provided by AISystem or another orchestrator.

    current_file_path = Path(__file__).resolve()
    # Assuming this file is in optimized_project/core/tools/
    # optimized_project_root is then parent.parent
    optimized_project_root = current_file_path.parent.parent

    # Need to temporarily add data_management to sys.path to import DatabaseManager for the example
    import sys
    sys.path.insert(0, str(optimized_project_root))
    from data_management.database import DatabaseManager

    print(f"Running AvailabilityTool example from: {current_file_path}")
    print(f"Determined project root for example: {optimized_project_root}")

    # Initialize DatabaseManager for the tool
    # This will create/use a DB at optimized_project/data/databases/employees.db
    db_man = DatabaseManager(project_root_path=optimized_project_root)

    # Example: Ensure at least one employee exists for testing
    # success, msg = db_man.create_employee("test_avail_user", "Test Available User", "Tester", "Tests things", "Python, Testing", "Write tests")
    # if success: print(msg)
    # else: print(f"Skipping user creation or error: {msg}")
    # db_man.update_employee_status("test_avail_user", "Available")


    tool = AvailabilityTool(db_manager_instance=db_man)

    print("\n--- General Availability ---")
    print(tool.run(exclude_username="another_user_to_exclude")) # Test with exclusion

    print("\n--- Availability for 'Python' expertise ---")
    python_experts = tool.get_best_available_for_expertise("Python")
    if python_experts:
        print(f"Found {len(python_experts)} expert(s) for Python:")
        for expert in python_experts:
            print(f"  - {expert['full_name']} ({expert['availability_status']})")
    else:
        print("No Python experts found or available.")

    print("\n--- Is 'test_avail_user' available for assignment? ---")
    # is_avail = tool.is_employee_available_for_assignment("test_avail_user")
    # print(f"'test_avail_user' available for assignment: {is_avail}")

    print("\nExample finished.")

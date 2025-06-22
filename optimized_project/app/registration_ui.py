"""
Employee registration and management UI for the Optimized Streamlit app.
"""

import streamlit as st
from typing import Dict, Any, List # For type hinting
from pathlib import Path
from datetime import datetime # For formatting dates if needed by UI directly

# Assuming this file is in optimized_project/app/
OPTIMIZED_PROJECT_ROOT_REG_UI = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT_REG_UI) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT_REG_UI))
    # No need to store sys.path in session_state from here, main_app does it once.

from config import app_config # From optimized_project/config/app_config.py
# DatabaseManager instance will be passed as an argument to functions needing it.
# from data_management.database import DatabaseManager

# Helper to format datetime strings, can be moved to a shared utils if used elsewhere
def _format_datetime_for_display(datetime_str: Optional[str]) -> str:
    if not datetime_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return datetime_str # Return original if parsing fails or not a string


def show_registration_form(db_manager: Any, for_admin_panel: bool = False):
    """
    Displays the employee registration form.
    Args:
        db_manager: An instance of DatabaseManager.
        for_admin_panel: If True, adjusts title and behavior for admin panel usage.
    """
    if not for_admin_panel:
        st.title("🏢 Employee Registration")
        st.markdown("### Create Your Employee Account")
        st.markdown("Please fill out all the information below to create your employee account.")
    else:
        st.subheader("📝 Register New Employee")

    form_key = "employee_registration_form_admin" if for_admin_panel else "employee_registration_form_public"

    with st.form(key=form_key):
        st.markdown("#### 👤 Basic Information")
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username *", placeholder="e.g., john.doe", key=f"{form_key}_username")
        with col2:
            full_name = st.text_input("Full Name *", placeholder="e.g., John Doe", key=f"{form_key}_fullname")

        st.markdown("#### 💼 Professional Information")
        # Simplified role list for example
        roles = ["", "Software Engineer", "Data Scientist", "Product Manager", "Support Specialist", "Other"]
        role_in_company = st.selectbox("Role in Company *", roles, key=f"{form_key}_role")
        if role_in_company == "Other":
            role_in_company = st.text_input("Please specify your role *", key=f"{form_key}_role_other")

        job_description = st.text_area("Job Description *", placeholder="Main responsibilities...", height=100, key=f"{form_key}_jobdesc")

        st.markdown("#### 🎯 Skills & Expertise")
        expertise = st.text_area("Areas of Expertise *", placeholder="e.g., Python, AI, Customer Support", height=100, key=f"{form_key}_expertise")
        responsibilities = st.text_area("Key Responsibilities *", placeholder="e.g., Develop features, Resolve tickets", height=100, key=f"{form_key}_responsibilities")

        st.markdown("---")
        submit_button = st.form_submit_button("Create Employee Account", use_container_width=True, type="primary")

        if submit_button:
            errors = _validate_registration_input(username, full_name, role_in_company, job_description, expertise, responsibilities)
            if errors:
                for error in errors: st.error(f"• {error}")
            else:
                success, message = db_manager.create_employee(
                    username=username.strip().lower(), full_name=full_name.strip(),
                    role_in_company=role_in_company.strip(), job_description=job_description.strip(),
                    expertise=expertise.strip(), responsibilities=responsibilities.strip()
                )
                if success:
                    st.success(f"✅ {message}")
                    if not for_admin_panel: # Public registration
                        st.info("You can now use your username to login.")
                        st.session_state[app_config.SESSION_KEYS["registration_success"]] = True
                else:
                    st.error(f"❌ Registration failed: {message}")

    if not for_admin_panel and st.session_state.get(app_config.SESSION_KEYS["registration_success"], False):
        st.markdown("---")
        if st.button("🔐 Go to Login", use_container_width=True, key=f"{form_key}_go_login"):
            st.session_state[app_config.SESSION_KEYS["show_registration"]] = False
            del st.session_state[app_config.SESSION_KEYS["registration_success"]] # Clean up flag
            st.rerun()

def _validate_registration_input(username, full_name, role, job_desc, expertise, resp) -> List[str]:
    errors = []
    if not username.strip() or len(username.strip()) < 3 or not username.replace(".", "").replace("_", "").isalnum():
        errors.append("Username must be at least 3 chars, alphanumeric with dots/underscores.")
    if not full_name.strip() or len(full_name.strip()) < 2: errors.append("Full name is required (min 2 chars).")
    if not role or not role.strip(): errors.append("Role in company is required.")
    if not job_desc.strip() or len(job_desc.strip()) < 10: errors.append("Job description is required (min 10 chars).")
    if not expertise.strip() or len(expertise.strip()) < 5: errors.append("Expertise is required (min 5 chars).")
    if not resp.strip() or len(resp.strip()) < 10: errors.append("Responsibilities are required (min 10 chars).")
    return errors


def _display_employee_list_ui(db_manager: Any):
    """UI to display list of registered employees (for admin panel)."""
    st.subheader("👥 Registered Employees List")
    if st.button("🔄 Refresh Status & List", key="admin_refresh_emp_list"):
        st.rerun()

    db_manager.auto_cleanup_expired_statuses() # Cleanup before fetching
    all_employees = db_manager.get_all_employees(active_only=False) # Show all, active or not

    if not all_employees:
        st.info("No employees registered yet.")
        return

    # Live Availability Summary
    status_counts = {'Available': 0, 'In Meeting': 0, 'Busy': 0, 'Do Not Disturb': 0, 'Offline': 0}
    active_emp_count = 0
    for emp_summary in all_employees:
        if emp_summary.get('is_active', True):
            active_emp_count +=1
            availability = db_manager.get_employee_availability(emp_summary['username'])
            current_status = availability.get('availability_status', 'Offline') if availability else 'Offline'
            if current_status in status_counts: status_counts[current_status] += 1
            else: status_counts['Offline'] +=1 # Default to offline if status unknown

    st.markdown("#### 📊 Live Availability Summary (Active Employees)")
    cols = st.columns(len(status_counts))
    for i, (status_name, count) in enumerate(status_counts.items()):
        cols[i].metric(f"{status_name}", count)

    st.markdown("---")
    search_term = st.text_input("🔍 Search employees (name, role, expertise)", key="admin_emp_search")

    employees_to_display = db_manager.search_employees(search_term) if search_term else all_employees
    if not employees_to_display and search_term:
        st.warning(f"No employees found matching '{search_term}'. Displaying all.")
        employees_to_display = all_employees # Show all if search yields nothing

    status_indicators = {'Available': '🟢', 'In Meeting': '🔴', 'Busy': '🟡', 'Do Not Disturb': '🔴', 'Offline': '⚫'}

    for emp in employees_to_display:
        availability = db_manager.get_employee_availability(emp['username'])
        current_status = availability.get('availability_status', 'Offline') if availability else 'Offline'
        status_led = status_indicators.get(current_status, '⚫')
        account_status_icon = "✅ Active" if emp.get('is_active', True) else "❌ Inactive"

        exp_title = f"{status_led} {emp['full_name']} ({emp['role_in_company']}) - Status: {current_status} | Account: {account_status_icon}"
        with st.expander(exp_title):
            st.write(f"**Username:** {emp['username']}")
            st.write(f"**Registered:** {_format_datetime_for_display(emp['created_at'])}")
            st.write(f"**Last Seen:** {_format_datetime_for_display(availability.get('last_seen')) if availability else 'N/A'}")
            if availability and current_status == 'In Meeting' and availability.get('status_until'):
                 st.write(f"**In Meeting Until:** {_format_datetime_for_display(availability['status_until'])}")
            st.write(f"**Expertise:** {emp['expertise']}")
            st.write(f"**Job Description:** {emp['job_description']}")
            st.write(f"**Responsibilities:** {emp['responsibilities']}")
            # Add edit/deactivate buttons here if needed for admin


def _display_employee_stats_ui(db_manager: Any):
    st.subheader("📊 Employee Statistics")
    stats = db_manager.get_employee_stats()
    if "error" in stats: st.error(f"Error loading stats: {stats['error']}"); return

    st.metric("Total Active Employees", stats.get('total_active', 0))
    st.metric("Total Registered Accounts", stats.get('total_all', 0))
    if stats.get('role_distribution'):
        st.markdown("#### Role Distribution (Active Employees)")
        for role, count in stats['role_distribution'].items(): st.write(f"- **{role}:** {count}")
    st.caption(f"Database: {stats.get('database_path', 'N/A')}")


def _display_backup_tools_ui(db_manager: Any):
    st.subheader("💾 Database Backup")
    if st.button("Create Database Backup", use_container_width=True, key="admin_backup_db"):
        success, message = db_manager.backup_database()
        if success: st.success(f"✅ {message}")
        else: st.error(f"❌ {message}")
    st.info("Regular backups are recommended.")


def _display_bulk_actions_ui(db_manager: Any):
    """UI for bulk employee actions."""
    st.subheader("🔄 Bulk Employee Availability Actions")
    st.markdown("These actions affect ALL active employees.")

    active_employees = [e for e in db_manager.get_all_employees() if e.get('is_active', True)]
    if not active_employees: st.warning("No active employees to perform bulk actions on."); return

    target_status = st.selectbox("Select status to apply to all active employees:",
                                 ['Available', 'Offline', 'Busy', 'In Meeting', 'Do Not Disturb'],
                                 key="bulk_status_select")

    confirm_bulk_action = st.checkbox(f"Confirm: Set all {len(active_employees)} active employees to '{target_status}'?", key="confirm_bulk_action")

    if st.button(f"Apply '{target_status}' to All Active Employees", disabled=not confirm_bulk_action, use_container_width=True, type="primary"):
        updated_count = 0; error_count = 0
        with st.spinner(f"Updating employees to '{target_status}'..."):
            for emp in active_employees:
                success, _ = db_manager.update_employee_status(emp['username'], target_status)
                if success: updated_count += 1
                else: error_count += 1
        st.success(f"Successfully updated {updated_count} employees to '{target_status}'.")
        if error_count > 0: st.error(f"Failed to update {error_count} employees.")
        st.rerun()
    st.warning("⚠️ This action cannot be undone easily. Use with caution.")


def show_employee_management(db_manager: Any):
    """Main UI for the admin employee management panel."""
    st.title("👥 Employee Management Panel")

    # Use a passed db_manager instance
    if not db_manager:
        st.error("Database Manager not available for Employee Management.")
        return

    tab_titles = ["View Employees", "Register New Employee", "Statistics", "Bulk Actions", "Backup Tools"]
    tab_view, tab_register, tab_stats, tab_bulk, tab_backup = st.tabs(tab_titles)

    with tab_view:
        _display_employee_list_ui(db_manager)
    with tab_register:
        show_registration_form(db_manager, for_admin_panel=True)
    with tab_stats:
        _display_employee_stats_ui(db_manager)
    with tab_bulk:
        _display_bulk_actions_ui(db_manager)
    with tab_backup:
        _display_backup_tools_ui(db_manager)

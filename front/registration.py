"""
Employee registration form for Streamlit app.
Allows new employees to register with their information.
"""

import streamlit as st
from typing import Dict, Any
from database import db_manager


def show_registration_form():
    """Display the employee registration form."""
    st.title("🏢 Employee Registration")
    st.markdown("### Create Your Employee Account")
    st.markdown("Please fill out all the information below to create your employee account.")
    
    with st.form("employee_registration_form"):
        # Basic Information Section
        st.markdown("#### 👤 Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "Username *",
                placeholder="e.g., john.doe",
                help="This will be your login username. Use only letters, numbers, and dots/underscores."
            )
        
        with col2:
            full_name = st.text_input(
                "Full Name *",
                placeholder="e.g., John Doe",
                help="Your complete first and last name"
            )
        
        # Professional Information Section
        st.markdown("#### 💼 Professional Information")
        
        role_in_company = st.selectbox(
            "Role in Company *",
            [
                "",  # Empty option
                "Software Engineer",
                "Data Scientist",
                "Product Manager",
                "DevOps Engineer",
                "UI/UX Designer",
                "Quality Assurance Engineer",
                "Business Analyst",
                "Project Manager",
                "Technical Lead",
                "Marketing Specialist",
                "Sales Representative",
                "Customer Support",
                "HR Specialist",
                "Finance Analyst",
                "Operations Manager",
                "Other"
            ],
            help="Select your primary role in the company"
        )
        
        if role_in_company == "Other":
            role_in_company = st.text_input(
                "Please specify your role *",
                placeholder="Enter your specific role"
            )
        
        job_description = st.text_area(
            "Job Description *",
            placeholder="Describe your main job responsibilities and what you do on a daily basis...",
            height=100,
            help="Provide a clear description of your role and main responsibilities"
        )
        
        # Skills and Expertise Section
        st.markdown("#### 🎯 Skills & Expertise")
        
        expertise = st.text_area(
            "Areas of Expertise *",
            placeholder="e.g., Python programming, Machine Learning, Project Management, UI Design...",
            height=100,
            help="List your key skills, technologies, and areas of expertise (separate with commas)"
        )
        
        responsibilities = st.text_area(
            "Key Responsibilities *",
            placeholder="e.g., Develop web applications, Manage team of 5 developers, Analyze business requirements...",
            height=100,
            help="Describe your main responsibilities and what you're accountable for"
        )
        
        # Form submission
        st.markdown("---")
        submit_button = st.form_submit_button(
            "Create Employee Account",
            use_container_width=True,
            type="primary"
        )
        
        if submit_button:
            # Validate required fields
            errors = []
            
            if not username.strip():
                errors.append("Username is required")
            elif len(username.strip()) < 3:
                errors.append("Username must be at least 3 characters long")
            elif not username.replace(".", "").replace("_", "").isalnum():
                errors.append("Username can only contain letters, numbers, dots, and underscores")
            
            if not full_name.strip():
                errors.append("Full name is required")
            elif len(full_name.strip()) < 2:
                errors.append("Full name must be at least 2 characters long")
            
            if not role_in_company or not role_in_company.strip():
                errors.append("Role in company is required")
            
            if not job_description.strip():
                errors.append("Job description is required")
            elif len(job_description.strip()) < 10:
                errors.append("Job description must be at least 10 characters long")
            
            if not expertise.strip():
                errors.append("Areas of expertise is required")
            elif len(expertise.strip()) < 5:
                errors.append("Areas of expertise must be at least 5 characters long")
            
            if not responsibilities.strip():
                errors.append("Key responsibilities is required")
            elif len(responsibilities.strip()) < 10:
                errors.append("Key responsibilities must be at least 10 characters long")
            
            # Show errors if any
            if errors:
                st.error("Please fix the following errors:")
                for error in errors:
                    st.error(f"• {error}")
            else:
                # Try to create the employee account
                success, message = db_manager.create_employee(
                    username=username.strip().lower(),
                    full_name=full_name.strip(),
                    role_in_company=role_in_company.strip(),
                    job_description=job_description.strip(),
                    expertise=expertise.strip(),
                    responsibilities=responsibilities.strip()
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.success("Your employee account has been created successfully!")
                    st.info("You can now use your username to login to the system.")
                    
                    # Set flag for showing login button outside form
                    st.session_state.registration_success = True
                    
                    # Show created account details
                    with st.expander("📋 Account Summary", expanded=True):
                        st.write(f"**Username:** {username.strip().lower()}")
                        st.write(f"**Full Name:** {full_name.strip()}")
                        st.write(f"**Role:** {role_in_company.strip()}")
                        st.write(f"**Expertise:** {expertise.strip()}")
                    
                else:
                    st.error(f"❌ Registration failed: {message}")
    
    # Option to go back to login (outside the form)
    if st.session_state.get("registration_success", False):
        st.markdown("---")
        if st.button("🔐 Go to Login", use_container_width=True):
            st.session_state.show_registration = False
            st.session_state.registration_success = False
            st.rerun()


def show_employee_list():
    """Display list of registered employees (admin view)."""
    st.markdown("### 👥 Registered Employees")
    
    employees = db_manager.get_all_employees()
    
    if not employees:
        st.info("No employees registered yet.")
        return
    
    # Search functionality
    search_term = st.text_input("🔍 Search employees", placeholder="Search by name, role, or expertise...")
    
    if search_term:
        employees = db_manager.search_employees(search_term)
        if not employees:
            st.warning(f"No employees found matching '{search_term}'")
            return
    
    # Display employee cards
    for employee in employees:
        with st.expander(f"👤 {employee['full_name']} - {employee['role_in_company']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Username:** {employee['username']}")
                st.write(f"**Role:** {employee['role_in_company']}")
                st.write(f"**Status:** {'✅ Active' if employee['is_active'] else '❌ Inactive'}")
                st.write(f"**Registered:** {employee['created_at'][:10]}")
            
            with col2:
                st.write(f"**Expertise:**")
                st.write(employee['expertise'])
            
            st.write(f"**Job Description:**")
            st.write(employee['job_description'])
            
            st.write(f"**Responsibilities:**")
            st.write(employee['responsibilities'])


def show_employee_stats():
    """Display employee statistics."""
    st.markdown("### 📊 Employee Statistics")
    
    stats = db_manager.get_employee_stats()
    
    if "error" in stats:
        st.error(f"Error loading statistics: {stats['error']}")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Active Employees", stats['total_active'])
    
    with col2:
        st.metric("Total Registered", stats['total_all'])
    
    with col3:
        st.metric("Database Size", f"{len(stats['role_distribution'])} roles")
    
    # Role distribution
    if stats['role_distribution']:
        st.markdown("#### Role Distribution")
        
        for role, count in stats['role_distribution'].items():
            st.write(f"**{role}:** {count} employee(s)")
    
    # Database info
    st.markdown("#### Database Information")
    st.code(f"Database path: {stats['database_path']}")


def show_backup_tools():
    """Show database backup tools."""
    st.markdown("### 💾 Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Create Backup", use_container_width=True):
            success, message = db_manager.backup_database()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
    
    with col2:
        st.info("💡 Regular backups are recommended to protect employee data")


def show_employee_management():
    """Main employee management interface."""
    st.markdown("## 👥 Employee Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Register New", "👤 View Employees", "📊 Statistics", "💾 Backup"])
    
    with tab1:
        show_registration_form()
    
    with tab2:
        show_employee_list()
    
    with tab3:
        show_employee_stats()
    
    with tab4:
        show_backup_tools()

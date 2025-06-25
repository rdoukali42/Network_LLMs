"""
Modern ticket interface with service layer integration.
Enhanced with real-time updates, analytics, and professional error handling.
Includes backward compatibility with legacy features.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import time

from service_integration import (
    get_ticket_service, get_user_service, get_workflow_service,
    get_analytics_service, get_notification_service, get_event_bus,
    handle_service_errors, setup_real_time_updates, show_service_health_status,
    show_system_metrics, get_current_user_info, get_service_manager
)

# Legacy imports for backward compatibility
from database import db_manager
from tickets.ticket_manager import TicketManager
from tickets.call_interface import show_active_call_interface
from tickets.availability import render_availability_status
from tickets.smart_refresh import (
    init_smart_refresh, check_for_ticket_updates, 
    smart_refresh_controls, show_refresh_notifications
)
from tickets.ticket_processing import process_ticket_with_ai


def show_modern_ticket_interface():
    """Display the modernized ticket interface with service layer integration."""
    
    # Initialize legacy systems for backward compatibility
    init_legacy_compatibility()
    
    # Initialize real-time updates
    setup_real_time_updates()
    
    # Show service health in sidebar
    show_service_health_status()
    
    # Legacy availability status in sidebar
    render_availability_status()
    
    # Legacy smart refresh controls
    smart_refresh_controls()
    
    # Check for legacy voice calls
    if check_voice_call_status():
        return  # Exit early if showing call interface
    
    # Check for updates if smart refresh is enabled
    if st.session_state.get('smart_refresh_enabled', False):
        updates_detected = check_for_ticket_updates()
        if updates_detected:
            st.rerun()
    
    # Show notifications about detected changes
    show_refresh_notifications()
    
    # Header with enhanced user info
    render_enhanced_header()
    
    # Check for admin employee management
    if check_admin_employee_management():
        return  # Exit early if showing employee management
    
    # Check if user is an employee for additional tabs
    is_employee = check_if_employee()
    
    # Main content tabs
    if is_employee:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎫 My Tickets", 
            "➕ Create Ticket", 
            "👨‍💼 Assigned to Me",
            "📊 Analytics", 
            "🔔 Notifications",
            "⚙️ System Status"
        ])
        
        with tab3:
            show_assigned_tickets_tab()
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎫 My Tickets", 
            "➕ Create Ticket", 
            "📊 Analytics", 
            "🔔 Notifications",
            "⚙️ System Status"
        ])
    
    with tab1:
        show_user_tickets_tab()
    
    with tab2:
        show_create_ticket_tab()
    
    with tab4 if is_employee else tab3:
        show_analytics_tab()
    
    with tab5 if is_employee else tab4:
        show_notifications_tab()
    
    with tab6 if is_employee else tab5:
        show_system_status_tab()


def render_enhanced_header():
    """Render enhanced header with user info and system status."""
    
    # Get current user info
    user_info = get_current_user_info()
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.title("🎫 AI Ticket System")
        
        if user_info:
            st.markdown(f"""
                **Welcome {user_info['full_name']}** | 
                *{user_info['role']}* | 
                *{user_info['department']}*
            """)
        else:
            # Fallback to legacy user info
            user_display = st.session_state.get("user_full_name", st.session_state.get("username", "User"))
            user_role = st.session_state.get("user_role", "User")
            st.markdown(f"**Welcome {user_display}** | *{user_role}*")
    
    with col2:
        # Real-time refresh button
        if st.button("🔄 Refresh", help="Refresh all data"):
            st.cache_data.clear()
            # Clear cache to force full refresh
            st.session_state.cached_ticket_state = {}
            st.rerun()
    
    with col3:
        # Employee management for admin users
        if st.session_state.get("username") == "admin":
            if st.button("👥 Employees", help="Manage employees"):
                st.session_state.show_employee_management = not st.session_state.get("show_employee_management", False)
                st.rerun()
        else:
            # Quick action button for regular users
            if st.button("⚡ Quick Ticket", help="Create ticket quickly"):
                st.session_state.show_quick_create = True
                st.rerun()
    
    with col4:
        # Logout button
        if st.button("🚪 Logout"):
            from auth import logout
            logout()


def check_admin_employee_management():
    """Check if admin wants to show employee management."""
    
    if st.session_state.get("show_employee_management", False):
        try:
            from registration import show_employee_management
            show_employee_management()
            return True
        except ImportError:
            st.error("Employee management module not available.")
            st.session_state.show_employee_management = False
            return True
        except Exception as e:
            st.error(f"Error loading employee management: {str(e)}")
            st.session_state.show_employee_management = False
            return True
    
    return False


@handle_service_errors("Loading tickets")
def show_user_tickets_tab():
    """Show user tickets with enhanced filtering and real-time updates."""
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            ["open", "in_progress", "resolved", "closed"],
            default=["open", "in_progress"]
        )
    
    with col2:
        priority_filter = st.multiselect(
            "Filter by Priority", 
            ["Low", "Medium", "High", "Critical"],
            default=[]
        )
    
    with col3:
        date_range = st.selectbox(
            "Date Range",
            ["All Time", "Last 7 Days", "Last 30 Days", "This Month"]
        )
    
    # Search
    search_query = st.text_input("🔍 Search tickets...", placeholder="Search by title, description, or ID")
    
    # Get tickets using legacy system
    try:
        all_tickets = st.session_state.ticket_manager.get_user_tickets(st.session_state.username)
        
        # Apply filters
        filtered_tickets = []
        for ticket in all_tickets:
            # Status filter
            ticket_status = ticket['status'].lower()
            if status_filter and ticket_status not in [s.lower() for s in status_filter]:
                continue
            
            # Priority filter
            if priority_filter and ticket['priority'] not in priority_filter:
                continue
            
            # Search filter
            if search_query:
                search_text = f"{ticket['subject']} {ticket['description']} {ticket['id']}".lower()
                if search_query.lower() not in search_text:
                    continue
            
            filtered_tickets.append(ticket)
        
        if filtered_tickets:
            st.subheader(f"📋 Your Tickets ({len(filtered_tickets)})")
            
            # Sort tickets by creation date (newest first)
            filtered_tickets.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Display tickets in enhanced format
            for ticket in filtered_tickets:
                render_legacy_ticket_card(ticket)
        else:
            st.info("No tickets found matching your criteria.")
            
            # Suggest creating a ticket
            if st.button("➕ Create Your First Ticket"):
                st.session_state.show_quick_create = True
                st.rerun()
                
    except Exception as e:
        st.error(f"Failed to load tickets: {str(e)}")


def render_legacy_ticket_card(ticket):
    """Render a ticket card using legacy ticket format."""
    
    # Determine status and priority colors
    status_colors = {
        "open": "🔴",
        "in_progress": "🟡", 
        "resolved": "🟢",
        "closed": "⚫"
    }
    
    priority_colors = {
        "Low": "🔵",
        "Medium": "🟡",
        "High": "🟠", 
        "Critical": "🔴"
    }
    
    with st.expander(f"🎫 [{ticket['id']}] {ticket['subject']} - {ticket['status']}", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Category:** {ticket['category']}")
            st.write(f"**Priority:** {ticket['priority']}")
        
        with col2:
            st.write(f"**Status:** {ticket['status']}")
            st.write(f"**Created:** {format_datetime(ticket['created_at'])}")
        
        with col3:
            if ticket.get('assigned_to'):
                employee = db_manager.get_employee_by_username(ticket['assigned_to'])
                if employee:
                    st.write(f"**Assigned to:** {employee['full_name']}")
                    st.write(f"**Assignment Status:** {ticket.get('assignment_status', 'assigned').title()}")
                else:
                    st.write(f"**Assigned to:** {ticket['assigned_to']}")
            elif ticket['response_at']:
                st.write(f"**Responded:** {format_datetime(ticket['response_at'])}")
            else:
                st.write("**Responded:** Pending")
        
        st.markdown("**Description:**")
        st.write(ticket['description'])
        
        if ticket.get('employee_solution'):
            st.markdown("**Solution:**")
            st.success(ticket['employee_solution'])
        elif ticket['response']:
            st.markdown("**AI Response:**")
            st.info(ticket['response'])
        else:
            if ticket.get('assigned_to'):
                employee = db_manager.get_employee_by_username(ticket['assigned_to'])
                employee_name = employee['full_name'] if employee else ticket['assigned_to']
                st.warning(f"⏳ {employee_name} is working on your ticket...")
            else:
                st.warning("⏳ Waiting for response...")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"🔄 Request Update", key=f"update_{ticket['id']}"):
                st.info("Update requested! You'll be notified when there's new information.")
        
        with col2:
            if ticket['status'] not in ['resolved', 'closed']:
                if st.button(f"✅ Mark Resolved", key=f"resolve_{ticket['id']}"):
                    # Update ticket status in legacy system
                    tickets = st.session_state.ticket_manager.load_tickets()
                    for t in tickets:
                        if t["id"] == ticket['id']:
                            t["status"] = "resolved"
                            t["updated_at"] = datetime.now().isoformat()
                            break
                    st.session_state.ticket_manager.save_tickets(tickets)
                    st.success("Ticket marked as resolved!")
                    st.rerun()


def render_ticket_card(ticket):
    """Render an enhanced ticket card with real-time status."""
    
    # Determine status color
    status_colors = {
        "open": "🔴",
        "in_progress": "🟡", 
        "resolved": "🟢",
        "closed": "⚫"
    }
    
    priority_colors = {
        "low": "🔵",
        "medium": "🟡",
        "high": "🟠", 
        "urgent": "🔴"
    }
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"**#{ticket.id} - {ticket.title}**")
            if ticket.description:
                with st.expander("Description"):
                    st.write(ticket.description)
        
        with col2:
            st.markdown(f"{status_colors.get(ticket.status, '⚪')} **{ticket.status.title()}**")
        
        with col3:
            st.markdown(f"{priority_colors.get(ticket.priority, '⚪')} {ticket.priority.title()}")
        
        with col4:
            if st.button(f"View #{ticket.id}", key=f"view_{ticket.id}"):
                show_ticket_details(ticket.id)
        
        # Show creation date and last update
        st.caption(f"Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M')} | Last update: {ticket.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        st.divider()


@handle_service_errors("Creating ticket")
def show_create_ticket_tab():
    """Show enhanced ticket creation form with AI assistance."""
    
    st.subheader("➕ Create New Support Ticket")
    
    # Quick create option
    if st.session_state.get("show_quick_create", False):
        show_quick_ticket_form()
        return
    
    # Enhanced form with AI suggestions
    with st.form("create_ticket_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            title = st.text_input(
                "Ticket Title *", 
                placeholder="Brief description of your issue"
            )
            
            description = st.text_area(
                "Detailed Description *",
                placeholder="Please provide as much detail as possible about your issue...",
                height=150
            )
        
        with col2:
            priority = st.selectbox(
                "Priority",
                ["low", "medium", "high", "urgent"],
                index=1  # Default to medium
            )
            
            category = st.selectbox(
                "Category",
                ["general", "technical", "hr", "facilities", "access", "other"]
            )
            
            # AI suggestion based on description
            if description and len(description) > 20:
                with st.spinner("🤖 AI analyzing your request..."):
                    suggestions = get_ai_suggestions(description)
                    if suggestions:
                        st.info(f"💡 AI Suggestion: {suggestions}")
        
        # Form submission
        submitted = st.form_submit_button("🎫 Create Ticket", use_container_width=True)
        
        if submitted:
            if not title or not description:
                st.error("Please fill in both title and description.")
            else:
                create_new_ticket(title, description, priority, category)


def show_quick_ticket_form():
    """Show a quick ticket creation form."""
    st.subheader("⚡ Quick Ticket Creation")
    
    quick_issue = st.text_input(
        "What's your issue?", 
        placeholder="Describe your problem in one sentence..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎫 Create Quick Ticket", disabled=not quick_issue):
            if quick_issue:
                create_new_ticket(
                    title=quick_issue[:50] + ("..." if len(quick_issue) > 50 else ""),
                    description=quick_issue,
                    priority="medium",
                    category="general"
                )
    
    with col2:
        if st.button("📝 Full Form"):
            st.session_state.show_quick_create = False
            st.rerun()


@handle_service_errors("Creating ticket")
def create_new_ticket(title: str, description: str, priority: str, category: str):
    """Create a new ticket using both new service layer and legacy compatibility."""
    
    try:
        # Create ticket using legacy system for backward compatibility
        ticket_id = st.session_state.ticket_manager.create_ticket(
            user=st.session_state.username,
            category=category,
            priority=priority,
            subject=title,
            description=description
        )
        
        if ticket_id:
            st.success(f"✅ Ticket created successfully! Ticket ID: **{ticket_id}**")
            st.info("Your ticket has been submitted and will be processed by our AI system.")
            
            # Process ticket with AI using legacy system
            try:
                with st.spinner("🤖 Starting AI processing..."):
                    process_ticket_with_ai(ticket_id, title, description)
                    
            except Exception as e:
                st.warning(f"Ticket created but AI processing failed: {str(e)}")
            
            # Clear form
            st.session_state.show_quick_create = False
            
            # Refresh tickets
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to create ticket. Please try again.")
                
    except Exception as e:
        st.error(f"Error creating ticket: {str(e)}")


def show_analytics_tab():
    """Show analytics and metrics dashboard."""
    
    st.subheader("📊 Analytics Dashboard")
    
    # Show system metrics
    show_system_metrics()
    
    # Personal analytics using legacy system
    try:
        user_tickets = st.session_state.ticket_manager.get_user_tickets(st.session_state.username)
        
        # Calculate basic statistics
        total_tickets = len(user_tickets)
        resolved_tickets = len([t for t in user_tickets if t['status'] in ['resolved', 'closed']])
        open_tickets = len([t for t in user_tickets if t['status'] in ['open', 'in_progress']])
        
        st.subheader("📈 Your Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Tickets", total_tickets)
        
        with col2:
            st.metric("Resolved Tickets", resolved_tickets)
        
        with col3:
            st.metric("Open Tickets", open_tickets)
        
        # Additional metrics
        if user_tickets:
            col4, col5, col6 = st.columns(3)
            
            with col4:
                # Recent activity (last 7 days)
                recent_tickets = [t for t in user_tickets if 
                                (datetime.now() - datetime.fromisoformat(t['created_at'])).days <= 7]
                st.metric("Last 7 Days", len(recent_tickets))
            
            with col5:
                # Priority breakdown
                high_priority = len([t for t in user_tickets if t['priority'] in ['High', 'Critical']])
                st.metric("High Priority", high_priority)
            
            with col6:
                # Resolution rate
                resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
                st.metric("Resolution Rate", f"{resolution_rate:.1f}%")
        
        # Ticket trends chart
        if st.checkbox("Show Detailed Analytics"):
            user_stats = {
                "total_tickets": total_tickets,
                "resolved_tickets": resolved_tickets,
                "avg_resolution_time": 24.5  # Sample data
            }
            show_detailed_analytics(user_stats)
            
    except Exception as e:
        st.warning(f"Analytics not available: {str(e)}")
        
        # Fallback basic display
        st.info("📊 Analytics will be available once you create some tickets.")


def show_detailed_analytics(user_stats: Dict[str, Any]):
    """Show detailed analytics charts."""
    try:
        # Try to import plotly for advanced charts
        try:
            import plotly.express as px
            import pandas as pd
            
            # Sample data - in real implementation, this would come from analytics service
            data = {
                "Date": pd.date_range(start="2024-01-01", periods=30, freq="D"),
                "Tickets Created": [1, 2, 0, 1, 3, 1, 0, 2, 1, 1, 0, 1, 2, 1, 0, 1, 1, 2, 0, 1, 1, 0, 1, 2, 1, 0, 1, 1, 0, 2],
                "Tickets Resolved": [0, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 0, 1, 2, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 2, 1, 0, 1, 1, 1]
            }
            
            df = pd.DataFrame(data)
            
            # Create charts
            fig = px.line(df, x="Date", y=["Tickets Created", "Tickets Resolved"], 
                         title="Ticket Activity Over Time")
            st.plotly_chart(fig, use_container_width=True)
            
        except ImportError:
            # Fallback to simple analytics without plotly
            st.info("📊 Advanced analytics available with: `pip install plotly pandas`")
            
            # Simple text-based analytics
            st.subheader("📈 Simple Analytics")
            
            # Recent activity summary
            if "total_tickets" in user_stats:
                st.write(f"- Total tickets created: {user_stats['total_tickets']}")
            if "resolved_tickets" in user_stats:
                st.write(f"- Tickets resolved: {user_stats['resolved_tickets']}")
            if "avg_resolution_time" in user_stats:
                st.write(f"- Average resolution time: {user_stats['avg_resolution_time']:.1f} hours")
            
            # Show recent ticket trends using legacy data
            try:
                user_tickets = st.session_state.ticket_manager.get_user_tickets(st.session_state.username)
                if user_tickets:
                    recent_tickets = [t for t in user_tickets if 
                                    (datetime.now() - datetime.fromisoformat(t['created_at'])).days <= 30]
                    
                    st.write(f"- Tickets in last 30 days: {len(recent_tickets)}")
                    
                    # Status breakdown
                    status_counts = {}
                    for ticket in recent_tickets:
                        status = ticket['status']
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    if status_counts:
                        st.write("- Status breakdown:")
                        for status, count in status_counts.items():
                            st.write(f"  - {status.title()}: {count}")
                            
            except Exception:
                st.write("- Recent activity data not available")
        
    except Exception as e:
        st.warning(f"Could not load detailed analytics: {str(e)}")


def show_notifications_tab():
    """Show notifications and alerts."""
    
    st.subheader("🔔 Notifications")
    
    try:
        notification_service = get_notification_service()
        user_service = get_user_service()
        
        # Get user notifications
        user = user_service.get_user_profile(st.session_state.username)
        if user:
            notifications = notification_service.get_user_notifications(user.id)
            
            if notifications:
                for notification in notifications:
                    render_notification_card(notification)
            else:
                st.info("No notifications at this time.")
        
        # Notification preferences
        with st.expander("🔧 Notification Preferences"):
            col1, col2 = st.columns(2)
            
            with col1:
                email_notifications = st.checkbox("Email Notifications", value=True)
                sms_notifications = st.checkbox("SMS Notifications", value=False)
            
            with col2:
                in_app_notifications = st.checkbox("In-App Notifications", value=True)
                push_notifications = st.checkbox("Push Notifications", value=True)
            
            if st.button("💾 Save Preferences"):
                # Save preferences using notification service
                preferences = {
                    "email": email_notifications,
                    "sms": sms_notifications,
                    "in_app": in_app_notifications,
                    "push": push_notifications
                }
                # notification_service.update_user_preferences(user.id, preferences)
                st.success("Preferences saved!")
                
    except Exception as e:
        st.warning(f"Notifications not available: {str(e)}")


def render_notification_card(notification):
    """Render a notification card."""
    
    # Notification type icons
    type_icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    icon = type_icons.get(notification.get("type", "info"), "📢")
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"{icon} **{notification.get('title', 'Notification')}**")
            st.write(notification.get('message', ''))
            st.caption(f"Received: {notification.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M')}")
        
        with col2:
            if not notification.get('read', False):
                if st.button("Mark Read", key=f"read_{notification.get('id')}"):
                    # Mark as read
                    st.rerun()
        
        st.divider()


def show_system_status_tab():
    """Show system status and health monitoring."""
    
    st.subheader("⚙️ System Status")
    
    # Service health overview
    service_manager = get_service_manager()
    health_status = service_manager.get_health_status()
    
    # Overall status
    if health_status["healthy"]:
        st.success("🟢 All systems operational")
    else:
        st.error("🔴 Some systems experiencing issues")
    
    # Detailed service status
    st.subheader("Service Details")
    
    for service_name, status in health_status["services"].items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{service_name.title()} Service**")
        
        with col2:
            if status.get("status") == "running":
                st.success("✅ Running")
            else:
                st.error("❌ Error")
        
        with col3:
            if status.get("message"):
                st.caption(status["message"])
    
    # System metrics
    st.subheader("Performance Metrics")
    show_system_metrics()
    
    # Recent errors
    if health_status["errors"]:
        st.subheader("Recent Issues")
        for error in health_status["errors"]:
            st.warning(f"⚠️ {error}")


@handle_service_errors("AI analysis")
def get_ai_suggestions(description: str) -> str:
    """Get AI suggestions for ticket categorization and priority."""
    try:
        workflow_service = get_workflow_service()
        
        # Simple AI analysis for category and priority suggestion
        if any(word in description.lower() for word in ["password", "login", "access", "account"]):
            return "This looks like an access issue. Consider 'high' priority if it's blocking work."
        elif any(word in description.lower() for word in ["urgent", "critical", "down", "broken"]):
            return "This seems urgent. Consider 'urgent' or 'high' priority."
        elif any(word in description.lower() for word in ["hr", "policy", "benefits", "time off"]):
            return "This appears to be an HR-related request. Category: 'hr'"
        else:
            return "Please provide more details for better AI assistance."
            
    except Exception:
        return ""


def show_ticket_details(ticket_id: int):
    """Show detailed ticket view with real-time updates."""
    
    try:
        ticket_service = get_ticket_service()
        ticket = ticket_service.get_ticket_by_id(ticket_id)
        
        if ticket:
            st.subheader(f"🎫 Ticket #{ticket.id} - {ticket.title}")
            
            # Ticket details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Description:**")
                st.write(ticket.description)
                
                # Show conversation/updates
                if hasattr(ticket, 'conversation') and ticket.conversation:
                    st.write("**Conversation:**")
                    for message in ticket.conversation:
                        st.chat_message(message.get("role", "user")).write(message.get("content", ""))
            
            with col2:
                st.write(f"**Status:** {ticket.status}")
                st.write(f"**Priority:** {ticket.priority}")
                st.write(f"**Category:** {ticket.category}")
                st.write(f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                # Actions
                if ticket.status != "closed":
                    if st.button("🔄 Request Update"):
                        st.info("Update requested! You'll be notified when there's new information.")
                    
                    if st.button("✅ Mark Resolved"):
                        # Update ticket status
                        ticket_service.update_ticket(ticket_id, {"status": "resolved"})
                        st.success("Ticket marked as resolved!")
                        st.rerun()
        else:
            st.error("Ticket not found.")
            
    except Exception as e:
        st.error(f"Error loading ticket details: {str(e)}")


def init_legacy_compatibility():
    """Initialize legacy systems for backward compatibility."""
    
    # Initialize smart refresh system
    init_smart_refresh()
    
    # Initialize ticket manager
    if "ticket_manager" not in st.session_state:
        st.session_state.ticket_manager = TicketManager()

    # Initialize workflow client (legacy)
    if "workflow_client" not in st.session_state:
        from workflow_client import WorkflowClient
        st.session_state.workflow_client = WorkflowClient()
    
    # Initialize voice call session states
    if "incoming_call" not in st.session_state:
        st.session_state.incoming_call = False
    if "call_active" not in st.session_state:
        st.session_state.call_active = False
    if "call_info" not in st.session_state:
        st.session_state.call_info = None
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "vocal_chat" not in st.session_state:
        st.session_state.vocal_chat = None


def check_if_employee() -> bool:
    """Check if current user is an employee."""
    try:
        employees = db_manager.get_all_employees()
        return st.session_state.username in [emp['username'] for emp in employees]
    except Exception as e:
        st.warning(f"Could not check employee status: {str(e)}")
        return False


def check_voice_call_status():
    """Check for active voice calls and handle call interface."""
    
    # Show active call interface if call is in progress
    if st.session_state.get('call_active', False) and st.session_state.get('call_info'):
        show_active_call_interface()
        return True
    
    # Check for incoming calls
    try:
        call_notifications = db_manager.get_call_notifications(st.session_state.username)
        if call_notifications:
            st.session_state.incoming_call = True
            st.session_state.call_info = call_notifications[0]['call_info']
            
            # Show incoming call notification
            with st.sidebar:
                st.warning("📞 Incoming Call!")
                if st.button("Answer Call", key="answer_call"):
                    st.session_state.call_active = True
                    st.session_state.incoming_call = False
                    # Mark call as answered
                    db_manager.mark_call_answered(call_notifications[0]['id'])
                    st.rerun()
                    
                if st.button("Decline Call", key="decline_call"):
                    st.session_state.incoming_call = False
                    # Mark call as declined
                    db_manager.mark_call_declined(call_notifications[0]['id'])
                    st.rerun()
    except Exception as e:
        pass  # Silently handle call notification errors
    
    return False


def show_assigned_tickets_tab():
    """Show tickets assigned to the current employee with modern enhancements."""
    
    st.subheader("👨‍💼 Tickets Assigned to Me")
    
    # Refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Assignments", key="refresh_assigned_tickets"):
            st.rerun()
    
    try:
        # Get assigned tickets from legacy system
        assigned_tickets = st.session_state.ticket_manager.get_assigned_tickets(st.session_state.username)
        
        if not assigned_tickets:
            st.info("No tickets are currently assigned to you.")
            return
        
        # Sort tickets by assignment date (newest first)
        assigned_tickets.sort(key=lambda x: x.get("assignment_date", ""), reverse=True)
        
        # Display tickets with enhanced interface
        for ticket in assigned_tickets:
            render_assigned_ticket_card(ticket)
            
    except Exception as e:
        st.error(f"Failed to load assigned tickets: {str(e)}")


def render_assigned_ticket_card(ticket):
    """Render an assigned ticket card with employee actions."""
    
    status_color = {
        "assigned": "🟡",
        "in_progress": "🔵", 
        "completed": "🟢"
    }.get(ticket.get("assignment_status", "assigned"), "⚪")
    
    with st.expander(f"{status_color} [{ticket['id']}] {ticket['subject']} - {ticket.get('assignment_status', 'assigned').title()}", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**From:** {ticket['user']}")
            st.write(f"**Category:** {ticket['category']}")
            st.write(f"**Priority:** {ticket['priority']}")
            st.write(f"**Assigned:** {format_datetime(ticket.get('assignment_date', ''))}")
        
        with col2:
            st.write(f"**Status:** {ticket.get('assignment_status', 'assigned').title()}")
            if ticket.get('completion_date'):
                st.write(f"**Completed:** {format_datetime(ticket['completion_date'])}")
        
        st.markdown("**Description:**")
        st.write(ticket['description'])
        
        # Solution interface for employees
        if ticket.get('assignment_status') != 'completed':
            render_employee_solution_interface(ticket)
        else:
            st.markdown("**Your Solution:**")
            st.success(ticket.get('employee_solution', 'No solution provided'))


def render_employee_solution_interface(ticket):
    """Render the employee solution interface."""
    
    st.markdown("**Provide Solution:**")
    solution_key = f"solution_{ticket['id']}"
    solution = st.text_area(
        "Your solution:",
        placeholder="Provide a detailed solution to the user's issue...",
        height=150,
        key=solution_key
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(f"Submit Solution", key=f"submit_{ticket['id']}"):
            if solution.strip():
                # Mark interaction time to prevent auto-refresh disruption
                st.session_state._form_interaction_time = time.time()
                st.session_state.ticket_manager.update_employee_solution(ticket['id'], solution.strip())
                st.success("✅ Solution submitted successfully!")
                st.rerun()
            else:
                st.error("Please provide a solution before submitting.")
    
    with col2:
        if st.button(f"Mark In Progress", key=f"progress_{ticket['id']}"):
            # Mark interaction time to prevent auto-refresh disruption
            st.session_state._form_interaction_time = time.time()
            # Update assignment status to in_progress
            tickets = st.session_state.ticket_manager.load_tickets()
            for t in tickets:
                if t["id"] == ticket['id']:
                    t["assignment_status"] = "in_progress"
                    t["updated_at"] = datetime.now().isoformat()
                    break
            st.session_state.ticket_manager.save_tickets(tickets)
            st.success("✅ Ticket marked as in progress!")
            st.rerun()
    
    with col3:
        if st.button(f"📞 Call About This", key=f"call_{ticket['id']}"):
            initiate_voice_call_for_ticket(ticket)
    
    with col4:
        # Use AI assistance for solution
        if st.button(f"🤖 AI Assist", key=f"ai_assist_{ticket['id']}"):
            get_ai_solution_assistance(ticket)


def initiate_voice_call_for_ticket(ticket):
    """Initiate a voice call for a specific ticket."""
    
    # Mark interaction time to prevent auto-refresh disruption
    st.session_state._form_interaction_time = time.time()
    
    # Create call notification for the current employee (self-call)
    employee = db_manager.get_employee_by_username(st.session_state.username)
    if employee:
        call_info = {
            "ticket_id": ticket['id'],
            "employee_name": employee['full_name'],
            "employee_username": st.session_state.username,
            "ticket_subject": ticket['subject'],
            "ticket_data": ticket,
            "employee_data": employee,
            "caller_name": "Self-Call",
            "created_by": st.session_state.username
        }
        
        # Create call notification for the current employee
        success = db_manager.create_call_notification(
            target_employee=st.session_state.username,
            ticket_id=ticket['id'],
            ticket_subject=ticket['subject'],
            caller_name="Self-Call",
            call_info=call_info
        )
        
        if success:
            st.success("📞 Voice call initiated! Check the sidebar to answer.")
            st.rerun()
        else:
            st.error("Failed to start voice call.")
    else:
        st.error("Employee data not found.")


def get_ai_solution_assistance(ticket):
    """Get AI assistance for solving a ticket."""
    
    try:
        service_integration = st.session_state.get("service_integration")
        if not service_integration:
            from service_integration import ServiceIntegration
            service_integration = ServiceIntegration()
            st.session_state.service_integration = service_integration
        
        # Create AI query for solution assistance
        query = f"""
        Employee Solution Request:
        Ticket ID: {ticket['id']}
        Subject: {ticket['subject']}
        Description: {ticket['description']}
        Category: {ticket['category']}
        Priority: {ticket['priority']}
        
        Please provide a professional solution recommendation for this support ticket.
        """
        
        with st.spinner("🤖 Getting AI assistance..."):
            result = service_integration.process_workflow_query(query, username=st.session_state.get('username', 'anonymous'))
            
            if result and isinstance(result, dict):
                ai_suggestion = (result.get("result") or 
                               result.get("synthesis") or 
                               result.get("response") or 
                               "AI assistance temporarily unavailable.")
            else:
                ai_suggestion = str(result) if result else "AI assistance temporarily unavailable."
            
            # Show AI suggestion in an info box
            st.info(f"🤖 AI Suggestion: {ai_suggestion}")
            
            # Option to use AI suggestion as solution
            if st.button(f"Use AI Suggestion", key=f"use_ai_{ticket['id']}"):
                st.session_state[f"solution_{ticket['id']}"] = ai_suggestion
                st.rerun()
                
    except Exception as e:
        st.warning(f"AI assistance not available: {str(e)}")


def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display."""
    try:
        if not datetime_str:
            return "N/A"
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(datetime_str) if datetime_str else "N/A"

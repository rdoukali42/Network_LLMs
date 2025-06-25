"""
Service layer integration for Streamlit frontend.
Provides centralized access to all backend services with caching and error handling.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# Add src to path for service imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import all services
from config.settings import Settings
from services.ticket_service import TicketService
from services.user_service import UserService  
from services.workflow_service import WorkflowService, WorkflowType
from services.notification_service import NotificationService
from services.analytics_service import AnalyticsService
from core.event_bus import EventBus
from utils.exceptions import AITicketSystemException


class ServiceManager:
    """
    Centralized service manager for the Streamlit frontend.
    
    Provides:
    - Service initialization and caching
    - Error handling and fallback mechanisms
    - Performance monitoring
    - Event-driven updates
    """
    
    def __init__(self):
        """Initialize the service manager."""
        self.logger = logging.getLogger(__name__)
        self._services: Dict[str, Any] = {}
        self._settings = None
        self._event_bus = None
        self._initialization_errors: List[str] = []
        
        # Initialize services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all backend services."""
        try:
            # Initialize settings
            self._settings = Settings()
            
            # Initialize event bus for real-time updates
            self._event_bus = EventBus()
            
            # Initialize repositories (needed for some services)
            from data.repositories.ticket_repository import TicketRepository
            from data.repositories.user_repository import UserRepository
            
            # Get proper database path without sqlite:// prefix
            db_path = self._settings.get_database_path()
            
            self.logger.info(f"[DEBUG] ServiceManager initializing with db_path: {db_path}")
            
            ticket_repo = TicketRepository()
            user_repo = UserRepository(db_path)
            
            self.logger.info(f"[DEBUG] ServiceManager created UserRepository with db_path: {user_repo.db_path}")
            
            # Initialize core services with proper dependencies
            user_service = UserService(user_repo, self._settings)
            ticket_service = TicketService(self._settings)
            
            self._services = {
                'ticket': ticket_service,
                'user': user_service,
                'workflow': WorkflowService(self._settings, ticket_service=ticket_service, user_service=user_service),
                'notification': NotificationService(self._settings),
                'analytics': AnalyticsService(ticket_repo, user_repo, self._settings)
            }
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize services: {str(e)}"
            self.logger.error(error_msg)
            self._initialization_errors.append(error_msg)
            
            # Initialize minimal services that don't require repositories
            try:
                # Even in fallback, use proper database path
                db_path = self._settings.get_database_path()
                fallback_user_repo = UserRepository(db_path)
                fallback_user_service = UserService(fallback_user_repo, self._settings)
                
                self._services = {
                    'ticket': TicketService(self._settings),
                    'user': fallback_user_service,
                    'workflow': WorkflowService(self._settings, user_service=fallback_user_service),
                    'notification': NotificationService(self._settings)
                }
                self.logger.info("Initialized core services in fallback mode with proper database path")
            except Exception as fallback_error:
                self.logger.error(f"Fallback initialization also failed: {str(fallback_error)}")
                self._services = {}
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            service_name: Name of the service ('ticket', 'user', 'workflow', etc.)
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service not found
        """
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        
        return self._services[service_name]
    
    def get_ticket_service(self) -> TicketService:
        """Get ticket service instance."""
        return self.get_service('ticket')
    
    def get_user_service(self) -> UserService:
        """Get user service instance."""
        return self.get_service('user')
    
    def get_workflow_service(self) -> WorkflowService:
        """Get workflow service instance."""
        return self.get_service('workflow')
    
    def get_notification_service(self) -> NotificationService:
        """Get notification service instance."""
        return self.get_service('notification')
    
    def get_analytics_service(self) -> AnalyticsService:
        """Get analytics service instance."""
        return self.get_service('analytics')
    
    def get_event_bus(self) -> EventBus:
        """Get event bus instance."""
        return self._event_bus
    
    def is_healthy(self) -> bool:
        """Check if all services are healthy."""
        return len(self._initialization_errors) == 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status of all services."""
        status = {
            "healthy": self.is_healthy(),
            "services": {},
            "errors": self._initialization_errors
        }
        
        for service_name, service in self._services.items():
            try:
                # Check if service has health check method
                if hasattr(service, 'health_check'):
                    service_status = service.health_check()
                else:
                    service_status = {"status": "running", "message": "No health check available"}
                
                status["services"][service_name] = service_status
                
            except Exception as e:
                status["services"][service_name] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return status


# Global service manager instance
@st.cache_resource
def get_service_manager() -> ServiceManager:
    """Get or create the global service manager instance."""
    return ServiceManager()


# Convenience functions for service access
def get_ticket_service() -> TicketService:
    """Get ticket service instance."""
    return get_service_manager().get_ticket_service()


def get_user_service() -> UserService:
    """Get user service instance."""
    return get_service_manager().get_user_service()


def get_workflow_service() -> WorkflowService:
    """Get workflow service instance."""
    return get_service_manager().get_workflow_service()


def get_notification_service() -> NotificationService:
    """Get notification service instance."""
    return get_service_manager().get_notification_service()


def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance."""
    return get_service_manager().get_analytics_service()


def get_event_bus() -> EventBus:
    """Get event bus instance."""
    return get_service_manager().get_event_bus()


# Enhanced error handling decorators
def handle_service_errors(operation_name: str = "Operation"):
    """
    Decorator to handle service errors gracefully in Streamlit.
    
    Args:
        operation_name: Name of the operation for error messages
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AITicketSystemException as e:
                st.error(f"{operation_name} failed: {e.message}")
                if hasattr(e, 'details') and e.details:
                    with st.expander("Error Details"):
                        st.json(e.details)
                return None
            except Exception as e:
                st.error(f"{operation_name} failed: {str(e)}")
                st.warning("Please try again or contact support if the issue persists.")
                return None
        
        return wrapper
    return decorator


# Real-time update functions
def setup_real_time_updates():
    """Setup real-time updates using the event bus."""
    try:
        event_bus = get_event_bus()
        
        # Subscribe to workflow events for real-time status updates
        def handle_workflow_update(event_data):
            """Handle workflow status updates."""
            if "workflow_updates" not in st.session_state:
                st.session_state.workflow_updates = []
            
            st.session_state.workflow_updates.append({
                "timestamp": datetime.now(),
                "event": event_data
            })
            
            # Trigger UI update
            st.rerun()
        
        # Subscribe to relevant events
        event_bus.subscribe("workflow.completed", handle_workflow_update)
        event_bus.subscribe("workflow.failed", handle_workflow_update)
        event_bus.subscribe("ticket.created", handle_workflow_update)
        event_bus.subscribe("ticket.updated", handle_workflow_update)
        
    except Exception as e:
        st.warning(f"Real-time updates not available: {str(e)}")


def show_service_health_status():
    """Display service health status in the sidebar."""
    service_manager = get_service_manager()
    health_status = service_manager.get_health_status()
    
    with st.sidebar:
        st.subheader("🏥 System Health")
        
        if health_status["healthy"]:
            st.success("All services operational")
        else:
            st.error("Some services have issues")
            
            # Show errors
            for error in health_status["errors"]:
                st.warning(f"⚠️ {error}")
        
        # Show individual service status
        with st.expander("Service Details"):
            for service_name, status in health_status["services"].items():
                if status.get("status") == "running":
                    st.success(f"✅ {service_name.title()}")
                else:
                    st.error(f"❌ {service_name.title()}: {status.get('message', 'Unknown error')}")


def show_system_metrics():
    """Display system metrics and performance indicators."""
    try:
        analytics_service = get_analytics_service()
        
        # Get real-time metrics with proper async handling
        try:
            import asyncio
            # Try to get running loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, we need to handle this differently
            metrics = {"active_tickets": 0, "resolved_today": 0, "avg_response_time": 0}
        except RuntimeError:
            # No event loop running, use asyncio.run
            try:
                metrics = asyncio.run(analytics_service.get_real_time_stats())
            except Exception:
                # Fallback to default metrics if async fails
                metrics = {"active_tickets": 0, "resolved_today": 0, "avg_response_time": 0}
        
        st.subheader("📊 System Metrics")
        
        # Display key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Active Tickets", 
                metrics.get("active_tickets", 0),
                delta=metrics.get("tickets_delta", 0)
            )
        
        with col2:
            st.metric(
                "Resolved Today", 
                metrics.get("resolved_today", 0),
                delta=metrics.get("resolved_delta", 0)
            )
        
        with col3:
            avg_time = metrics.get("avg_response_time", 0)
            st.metric(
                "Avg Response", 
                f"{avg_time:.1f}h" if avg_time > 0 else "N/A"
            )
        
        with col4:
            satisfaction = metrics.get("satisfaction_rate", 0)
            st.metric(
                "Satisfaction", 
                f"{satisfaction:.1f}%" if satisfaction > 0 else "N/A"
            )
        
    except Exception as e:
        st.warning(f"Metrics not available: {str(e)}")


def get_current_user_info() -> Optional[Dict[str, Any]]:
    """Get current user information from session and user service."""
    try:
        if "username" not in st.session_state:
            return None
        
        user_service = get_user_service()
        user_profile = user_service.get_user_profile(st.session_state.username)
        
        if user_profile:
            return {
                "username": user_profile.username,
                "full_name": user_profile.full_name,
                "role": user_profile.role_in_company,
                "department": user_profile.department,
                "email": user_profile.email_address
            }
        
        return None
        
    except Exception as e:
        st.warning(f"Could not load user information: {str(e)}")
        return None


class ServiceIntegration:
    """
    Service integration facade for frontend components.
    Provides a simplified interface to all backend services.
    """
    
    def __init__(self):
        """Initialize service integration."""
        self.service_manager = ServiceManager()
    
    def process_workflow_query(self, query: str, username: str = None, ticket_id: str = None) -> Dict[str, Any]:
        """Process a query through the workflow service."""
        try:
            # Use provided username or get from session state
            if not username:
                import streamlit as st
                username = st.session_state.get('username', 'anonymous')
            
            # Try to get workflow service
            if 'workflow' in self.service_manager._services:
                workflow_service = self.service_manager._services['workflow']
                return workflow_service.process_query(query, username=username, ticket_id=ticket_id)
            else:
                # Fallback to legacy workflow client
                try:
                    from workflow_client import WorkflowClient
                    client = WorkflowClient()
                    if client.is_ready():
                        return client.process_query(query, username=username)
                    else:
                        return {"error": "Workflow system not available"}
                except Exception as fallback_error:
                    return {"error": f"Workflow processing failed: {str(fallback_error)}"}
        except Exception as e:
            return {"error": f"Workflow processing failed: {str(e)}"}
    
    def is_healthy(self) -> bool:
        """Check if services are healthy."""
        try:
            return self.service_manager.is_healthy()
        except Exception:
            return False
    
    @property
    def multi_agent_workflow(self):
        """Get the multi-agent workflow instance for call completion and complex flows."""
        try:
            workflow_service = self.service_manager.get_workflow_service()
            return workflow_service.multi_agent_workflow
        except Exception as e:
            print(f"❌ ERROR: Failed to get multi_agent_workflow: {e}")
            return None

"""
Ticket service for managing ticket business logic.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from data.models.ticket import Ticket, TicketStatus, TicketPriority, TicketType
from data.models.user import User
from data.repositories.ticket_repository import TicketRepository
from data.repositories.user_repository import UserRepository
from core.base_service import BaseService
from utils.exceptions import ValidationError, BusinessLogicError
from utils.logging_config import get_logger


class TicketService(BaseService):
    """
    Service class handling ticket-related business logic.
    """
    
    def __init__(self, ticket_repository=None, settings=None):
        super().__init__(settings or "TicketService")
        self.ticket_repository = ticket_repository or TicketRepository()
        self.user_repository = UserRepository()
    
    def get_service_name(self) -> str:
        """Return the service name."""
        return "TicketService"
    
    def create_ticket(
        self, 
        user_id: int, 
        title: str, 
        description: str, 
        ticket_type: TicketType,
        priority: TicketPriority = TicketPriority.MEDIUM
    ) -> Ticket:
        """
        Create a new ticket.
        
        Args:
            user_id: ID of the user creating the ticket
            title: Ticket title
            description: Ticket description
            ticket_type: Type of the ticket
            priority: Priority level
            
        Returns:
            Created ticket
            
        Raises:
            ValidationError: If validation fails
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate inputs
            self._validate_ticket_creation(user_id, title, description, ticket_type, priority)
            
            # Check if user exists and is active
            user = self.user_repository.get_by_id(user_id)
            if not user or not user.is_active:
                raise BusinessLogicError(f"User {user_id} not found or inactive")
            
            # Create ticket object
            ticket = Ticket(
                title=title.strip(),
                description=description.strip(),
                ticket_type=ticket_type,
                priority=priority,
                user_id=user_id,
                status=TicketStatus.OPEN,
                created_at=datetime.now()
            )
            
            # Save to repository
            created_ticket = self.ticket_repository.create(ticket)
            
            self.logger.info(f"Ticket created: {created_ticket.id} by user {user_id}")
            
            # Trigger post-creation workflows
            self._trigger_ticket_created_workflow(created_ticket, user)
            
            return created_ticket
            
        except Exception as e:
            self.logger.error(f"Failed to create ticket: {e}")
            raise
    
    def update_ticket_status(
        self, 
        ticket_id: int, 
        new_status: TicketStatus, 
        updated_by: int,
        resolution: Optional[str] = None
    ) -> Ticket:
        """
        Update ticket status.
        
        Args:
            ticket_id: Ticket ID
            new_status: New status
            updated_by: User ID making the update
            resolution: Resolution text (required for resolved status)
            
        Returns:
            Updated ticket
        """
        try:
            # Get existing ticket
            ticket = self.ticket_repository.get_by_id(ticket_id)
            if not ticket:
                raise BusinessLogicError(f"Ticket {ticket_id} not found")
            
            # Validate status transition
            self._validate_status_transition(ticket.status, new_status)
            
            # Check permissions
            self._check_update_permissions(ticket, updated_by)
            
            # Handle status-specific logic
            if new_status == TicketStatus.RESOLVED:
                if not resolution:
                    raise ValidationError("Resolution is required when resolving a ticket")
                ticket.resolution = resolution
                ticket.resolved_at = datetime.now()
            
            # Update ticket
            ticket.status = new_status
            ticket.updated_at = datetime.now()
            
            # Save changes
            updated_ticket = self.ticket_repository.update(ticket)
            
            self.logger.info(f"Ticket {ticket_id} status updated to {new_status.value} by user {updated_by}")
            
            # Trigger status change workflows
            self._trigger_status_change_workflow(updated_ticket, new_status)
            
            return updated_ticket
            
        except Exception as e:
            self.logger.error(f"Failed to update ticket status: {e}")
            raise
    
    def assign_ticket(self, ticket_id: int, agent_name: str, assigned_by: int) -> Ticket:
        """
        Assign ticket to an agent.
        
        Args:
            ticket_id: Ticket ID
            agent_name: Name of the agent
            assigned_by: User ID making the assignment
            
        Returns:
            Updated ticket
        """
        try:
            ticket = self.ticket_repository.get_by_id(ticket_id)
            if not ticket:
                raise BusinessLogicError(f"Ticket {ticket_id} not found")
            
            # Check assignment permissions
            self._check_assignment_permissions(assigned_by)
            
            # Update assignment
            ticket.assigned_agent = agent_name
            ticket.status = TicketStatus.IN_PROGRESS
            ticket.updated_at = datetime.now()
            
            updated_ticket = self.ticket_repository.update(ticket)
            
            self.logger.info(f"Ticket {ticket_id} assigned to {agent_name} by user {assigned_by}")
            
            return updated_ticket
            
        except Exception as e:
            self.logger.error(f"Failed to assign ticket: {e}")
            raise
    
    def get_user_tickets(
        self, 
        user_id: int, 
        status_filter: Optional[TicketStatus] = None,
        limit: int = 50
    ) -> List[Ticket]:
        """
        Get tickets for a specific user.
        
        Args:
            user_id: User ID
            status_filter: Optional status filter
            limit: Maximum number of tickets to return
            
        Returns:
            List of user tickets
        """
        try:
            return self.ticket_repository.get_by_user_id(
                user_id=user_id,
                status=status_filter,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Failed to get user tickets: {e}")
            raise
    
    def get_tickets_by_status(self, status: TicketStatus, limit: int = 100) -> List[Ticket]:
        """Get tickets by status."""
        try:
            return self.ticket_repository.get_by_status(status, limit)
        except Exception as e:
            self.logger.error(f"Failed to get tickets by status: {e}")
            raise
    
    def search_tickets(
        self, 
        query: str, 
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Ticket]:
        """
        Search tickets by title or description.
        
        Args:
            query: Search query
            user_id: Optional user filter
            limit: Maximum results
            
        Returns:
            List of matching tickets
        """
        try:
            return self.ticket_repository.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Failed to search tickets: {e}")
            raise
    
    def get_ticket_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get ticket analytics for the specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics data
        """
        try:
            return self.ticket_repository.get_analytics(days)
        except Exception as e:
            self.logger.error(f"Failed to get ticket analytics: {e}")
            raise
    
    def _validate_ticket_creation(
        self, 
        user_id: int, 
        title: str, 
        description: str, 
        ticket_type: TicketType,
        priority: TicketPriority
    ):
        """Validate ticket creation parameters."""
        if not user_id or user_id <= 0:
            raise ValidationError("Valid user ID is required")
        
        if not title or len(title.strip()) < 3:
            raise ValidationError("Title must be at least 3 characters long")
        
        if len(title) > 200:
            raise ValidationError("Title cannot exceed 200 characters")
        
        if not description or len(description.strip()) < 10:
            raise ValidationError("Description must be at least 10 characters long")
        
        if len(description) > 5000:
            raise ValidationError("Description cannot exceed 5000 characters")
        
        if not isinstance(ticket_type, TicketType):
            raise ValidationError("Valid ticket type is required")
        
        if not isinstance(priority, TicketPriority):
            raise ValidationError("Valid priority is required")
    
    def _validate_status_transition(self, current_status: TicketStatus, new_status: TicketStatus):
        """Validate if status transition is allowed."""
        # Define allowed transitions
        allowed_transitions = {
            TicketStatus.OPEN: [TicketStatus.IN_PROGRESS, TicketStatus.PENDING_INFO, TicketStatus.CANCELLED],
            TicketStatus.IN_PROGRESS: [TicketStatus.RESOLVED, TicketStatus.PENDING_INFO, TicketStatus.OPEN],
            TicketStatus.PENDING_INFO: [TicketStatus.IN_PROGRESS, TicketStatus.OPEN, TicketStatus.CANCELLED],
            TicketStatus.RESOLVED: [TicketStatus.CLOSED, TicketStatus.OPEN],  # Can reopen
            TicketStatus.CLOSED: [TicketStatus.OPEN],  # Can reopen
            TicketStatus.CANCELLED: [TicketStatus.OPEN],  # Can reopen
        }
        
        if new_status not in allowed_transitions.get(current_status, []):
            raise BusinessLogicError(
                f"Status transition from {current_status.value} to {new_status.value} is not allowed"
            )
    
    def _check_update_permissions(self, ticket: Ticket, user_id: int):
        """Check if user has permission to update the ticket."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise BusinessLogicError("User not found")
        
        # Ticket owner can always update
        if ticket.user_id == user_id:
            return
        
        # Managers and admins can update any ticket
        if user.is_manager() or user.is_admin():
            return
        
        raise BusinessLogicError("Insufficient permissions to update this ticket")
    
    def _check_assignment_permissions(self, user_id: int):
        """Check if user has permission to assign tickets."""
        user = self.user_repository.get_by_id(user_id)
        if not user or not (user.is_manager() or user.is_admin()):
            raise BusinessLogicError("Insufficient permissions to assign tickets")
    
    def _trigger_ticket_created_workflow(self, ticket: Ticket, user: User):
        """Trigger workflows after ticket creation."""
        # This would integrate with the workflow engine
        # For now, just log the event
        self.logger.info(f"Ticket created workflow triggered for ticket {ticket.id}")
    
    def _trigger_status_change_workflow(self, ticket: Ticket, new_status: TicketStatus):
        """Trigger workflows after status change."""
        # This would integrate with the workflow engine
        # For now, just log the event
        self.logger.info(f"Status change workflow triggered for ticket {ticket.id} to {new_status.value}")

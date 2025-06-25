"""
Notification service for handling system notifications.
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from core.base_service import BaseService
from data.models.user import User
from utils.exceptions import ValidationError, BusinessLogicError
from config.settings import Settings
import json
import uuid

if TYPE_CHECKING:
    from services.user_service import UserService


class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    TICKET_UPDATE = "ticket_update"
    SYSTEM_ALERT = "system_alert"
    REMINDER = "reminder"
    WORKFLOW_STATUS = "workflow_status"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Notification data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = ""
    message: str = ""
    channels: List[NotificationChannel] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_read: bool = False
    is_sent: bool = False
    delivery_attempts: int = 0
    max_delivery_attempts: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "channels": [ch.value for ch in self.channels],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_read": self.is_read,
            "is_sent": self.is_sent,
            "delivery_attempts": self.delivery_attempts
        }


class NotificationService(BaseService):
    """
    Service for managing notifications and communication.
    """
    
    def __init__(self, settings, user_service=None):
        super().__init__(settings)
        self.user_service = user_service
        self._notifications: Dict[str, Notification] = {}
        self._user_notifications: Dict[int, List[str]] = {}
        self._templates: Dict[str, Dict[str, str]] = self._load_notification_templates()
    
    def get_service_name(self) -> str:
        """Return the service name."""
        return "NotificationService"
    
    async def get_supported_notification_types(self) -> List[str]:
        """
        Get list of supported notification types.
        
        Returns:
            List of supported notification type values
        """
        return [notification_type.value for notification_type in NotificationType]
    
    def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        channels: Optional[List[NotificationChannel]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_for: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new notification.
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            channels: Delivery channels (defaults to in-app)
            priority: Notification priority
            scheduled_for: When to send the notification
            expires_at: When the notification expires
            metadata: Additional metadata
            
        Returns:
            Notification ID
            
        Raises:
            ValidationError: If validation fails
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate inputs
            self._validate_notification_creation(user_id, title, message)
            
            # Set default channels
            if channels is None:
                channels = [NotificationChannel.IN_APP]
            
            # Create notification
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                priority=priority,
                title=title.strip(),
                message=message.strip(),
                channels=channels,
                scheduled_for=scheduled_for,
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            # Store notification
            self._notifications[notification.id] = notification
            
            # Add to user's notification list
            if user_id not in self._user_notifications:
                self._user_notifications[user_id] = []
            self._user_notifications[user_id].append(notification.id)
            
            self.logger.info(f"Notification created: {notification.id} for user {user_id}")
            
            # Send immediately if not scheduled
            if scheduled_for is None:
                self._send_notification(notification)
            
            return notification.id
            
        except Exception as e:
            self.logger.error(f"Failed to create notification: {e}")
            raise
    
    def send_ticket_notification(
        self,
        user_id: int,
        ticket_id: int,
        event_type: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a ticket-related notification.
        
        Args:
            user_id: User to notify
            ticket_id: Ticket ID
            event_type: Type of ticket event (created, updated, resolved, etc.)
            additional_info: Additional information
            
        Returns:
            Notification ID
        """
        try:
            # Get notification template
            template = self._get_ticket_notification_template(event_type)
            
            # Format message
            metadata = additional_info or {}
            metadata.update({"ticket_id": ticket_id, "event_type": event_type})
            
            title = template["title"].format(ticket_id=ticket_id, **metadata)
            message = template["message"].format(ticket_id=ticket_id, **metadata)
            
            # Determine priority based on event type
            priority = NotificationPriority.HIGH if event_type in ["resolved", "escalated"] else NotificationPriority.NORMAL
            
            return self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.TICKET_UPDATE,
                title=title,
                message=message,
                priority=priority,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send ticket notification: {e}")
            raise
    
    def send_workflow_notification(
        self,
        user_id: int,
        workflow_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a workflow status notification.
        
        Args:
            user_id: User to notify
            workflow_id: Workflow ID
            status: Workflow status
            result: Workflow result data
            
        Returns:
            Notification ID
        """
        try:
            # Get template
            template = self._get_workflow_notification_template(status)
            
            metadata = result or {}
            metadata.update({"workflow_id": workflow_id, "status": status})
            
            title = template["title"].format(workflow_id=workflow_id[:8], status=status, **metadata)
            message = template["message"].format(workflow_id=workflow_id[:8], status=status, **metadata)
            
            # Set priority based on status
            priority_map = {
                "completed": NotificationPriority.NORMAL,
                "failed": NotificationPriority.HIGH,
                "cancelled": NotificationPriority.LOW
            }
            priority = priority_map.get(status, NotificationPriority.NORMAL)
            
            return self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.WORKFLOW_STATUS,
                title=title,
                message=message,
                priority=priority,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send workflow notification: {e}")
            raise
    
    def send_system_alert(
        self,
        user_ids: List[int],
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.HIGH,
        channels: Optional[List[NotificationChannel]] = None
    ) -> List[str]:
        """
        Send system alert to multiple users.
        
        Args:
            user_ids: List of user IDs to notify
            title: Alert title
            message: Alert message
            priority: Alert priority
            channels: Delivery channels
            
        Returns:
            List of notification IDs
        """
        try:
            notification_ids = []
            
            for user_id in user_ids:
                notification_id = self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.SYSTEM_ALERT,
                    title=title,
                    message=message,
                    priority=priority,
                    channels=channels or [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
                    expires_at=datetime.now() + timedelta(days=7)  # System alerts expire in 7 days
                )
                notification_ids.append(notification_id)
            
            self.logger.info(f"System alert sent to {len(user_ids)} users")
            return notification_ids
            
        except Exception as e:
            self.logger.error(f"Failed to send system alert: {e}")
            raise
    
    def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: Return only unread notifications
            limit: Maximum number of notifications
            
        Returns:
            List of notifications
        """
        try:
            user_notification_ids = self._user_notifications.get(user_id, [])
            notifications = []
            
            for notification_id in user_notification_ids:
                if notification_id in self._notifications:
                    notification = self._notifications[notification_id]
                    
                    # Filter by read status if requested
                    if unread_only and notification.is_read:
                        continue
                    
                    # Check if notification has expired
                    if notification.expires_at and datetime.now() > notification.expires_at:
                        continue
                    
                    notifications.append(notification.to_dict())
            
            # Sort by creation date (newest first) and limit
            notifications.sort(key=lambda x: x["created_at"], reverse=True)
            return notifications[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get user notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str, user_id: int) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security check)
            
        Returns:
            True if marked as read
        """
        try:
            if notification_id not in self._notifications:
                return False
            
            notification = self._notifications[notification_id]
            
            # Check user ownership
            if notification.user_id != user_id:
                raise BusinessLogicError("Cannot mark notification for different user")
            
            notification.is_read = True
            
            self.logger.info(f"Notification marked as read: {notification_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    def mark_all_notifications_read(self, user_id: int) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        try:
            user_notification_ids = self._user_notifications.get(user_id, [])
            marked_count = 0
            
            for notification_id in user_notification_ids:
                if notification_id in self._notifications:
                    notification = self._notifications[notification_id]
                    if not notification.is_read:
                        notification.is_read = True
                        marked_count += 1
            
            self.logger.info(f"Marked {marked_count} notifications as read for user {user_id}")
            return marked_count
            
        except Exception as e:
            self.logger.error(f"Failed to mark all notifications as read: {e}")
            return 0
    
    def delete_notification(self, notification_id: str, user_id: int) -> bool:
        """
        Delete a notification.
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for security check)
            
        Returns:
            True if deleted
        """
        try:
            if notification_id not in self._notifications:
                return False
            
            notification = self._notifications[notification_id]
            
            # Check user ownership
            if notification.user_id != user_id:
                raise BusinessLogicError("Cannot delete notification for different user")
            
            # Remove from notifications
            del self._notifications[notification_id]
            
            # Remove from user's list
            if user_id in self._user_notifications:
                self._user_notifications[user_id] = [
                    nid for nid in self._user_notifications[user_id] 
                    if nid != notification_id
                ]
            
            self.logger.info(f"Notification deleted: {notification_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete notification: {e}")
            return False
    
    def get_notification_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get notification statistics.
        
        Args:
            user_id: Optional user ID to get stats for specific user
            
        Returns:
            Notification statistics
        """
        try:
            if user_id:
                user_notification_ids = self._user_notifications.get(user_id, [])
                user_notifications = [
                    self._notifications[nid] for nid in user_notification_ids 
                    if nid in self._notifications
                ]
                
                total = len(user_notifications)
                unread = sum(1 for n in user_notifications if not n.is_read)
                
                by_type = {}
                for notification in user_notifications:
                    ntype = notification.type.value
                    by_type[ntype] = by_type.get(ntype, 0) + 1
                
                return {
                    "user_id": user_id,
                    "total_notifications": total,
                    "unread_notifications": unread,
                    "read_notifications": total - unread,
                    "by_type": by_type,
                    "last_updated": datetime.now().isoformat()
                }
            else:
                # System-wide stats
                total = len(self._notifications)
                unread = sum(1 for n in self._notifications.values() if not n.is_read)
                
                by_type = {}
                by_priority = {}
                for notification in self._notifications.values():
                    ntype = notification.type.value
                    priority = notification.priority.value
                    by_type[ntype] = by_type.get(ntype, 0) + 1
                    by_priority[priority] = by_priority.get(priority, 0) + 1
                
                return {
                    "total_notifications": total,
                    "unread_notifications": unread,
                    "read_notifications": total - unread,
                    "by_type": by_type,
                    "by_priority": by_priority,
                    "active_users": len(self._user_notifications),
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get notification stats: {e}")
            return {"error": str(e)}
    
    def cleanup_expired_notifications(self) -> int:
        """
        Clean up expired notifications.
        
        Returns:
            Number of notifications cleaned up
        """
        try:
            current_time = datetime.now()
            expired_ids = []
            
            for notification_id, notification in self._notifications.items():
                if notification.expires_at and current_time > notification.expires_at:
                    expired_ids.append(notification_id)
            
            # Remove expired notifications
            for notification_id in expired_ids:
                notification = self._notifications[notification_id]
                user_id = notification.user_id
                
                del self._notifications[notification_id]
                
                if user_id in self._user_notifications:
                    self._user_notifications[user_id] = [
                        nid for nid in self._user_notifications[user_id] 
                        if nid != notification_id
                    ]
            
            if expired_ids:
                self.logger.info(f"Cleaned up {len(expired_ids)} expired notifications")
            
            return len(expired_ids)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired notifications: {e}")
            return 0
    
    def _send_notification(self, notification: Notification):
        """Send notification through specified channels."""
        try:
            for channel in notification.channels:
                if channel == NotificationChannel.IN_APP:
                    # In-app notifications are already stored
                    pass
                elif channel == NotificationChannel.EMAIL:
                    self._send_email_notification(notification)
                elif channel == NotificationChannel.SMS:
                    self._send_sms_notification(notification)
                elif channel == NotificationChannel.PUSH:
                    self._send_push_notification(notification)
                elif channel == NotificationChannel.SLACK:
                    self._send_slack_notification(notification)
            
            notification.is_sent = True
            notification.delivery_attempts += 1
            
        except Exception as e:
            self.logger.error(f"Failed to send notification {notification.id}: {e}")
            notification.delivery_attempts += 1
    
    def _send_email_notification(self, notification: Notification):
        """Send email notification (placeholder implementation)."""
        # This would integrate with an email service
        self.logger.info(f"Email notification sent: {notification.id}")
    
    def _send_sms_notification(self, notification: Notification):
        """Send SMS notification (placeholder implementation)."""
        # This would integrate with an SMS service
        self.logger.info(f"SMS notification sent: {notification.id}")
    
    def _send_push_notification(self, notification: Notification):
        """Send push notification (placeholder implementation)."""
        # This would integrate with a push notification service
        self.logger.info(f"Push notification sent: {notification.id}")
    
    def _send_slack_notification(self, notification: Notification):
        """Send Slack notification (placeholder implementation)."""
        # This would integrate with Slack API
        self.logger.info(f"Slack notification sent: {notification.id}")
    
    def _validate_notification_creation(self, user_id: int, title: str, message: str):
        """Validate notification creation parameters."""
        if not user_id or user_id <= 0:
            raise ValidationError("Valid user ID is required")
        
        if not title or len(title.strip()) < 1:
            raise ValidationError("Title is required")
        
        if len(title) > 200:
            raise ValidationError("Title cannot exceed 200 characters")
        
        if not message or len(message.strip()) < 1:
            raise ValidationError("Message is required")
        
        if len(message) > 1000:
            raise ValidationError("Message cannot exceed 1000 characters")
    
    def _load_notification_templates(self) -> Dict[str, Dict[str, str]]:
        """Load notification templates."""
        return {
            "ticket_created": {
                "title": "Ticket #{ticket_id} Created",
                "message": "Your support ticket has been created and assigned ID #{ticket_id}. We'll get back to you soon."
            },
            "ticket_updated": {
                "title": "Ticket #{ticket_id} Updated", 
                "message": "Your support ticket #{ticket_id} has been updated. Please check for new information."
            },
            "ticket_resolved": {
                "title": "Ticket #{ticket_id} Resolved",
                "message": "Great news! Your support ticket #{ticket_id} has been resolved. Please review the solution."
            },
            "ticket_escalated": {
                "title": "Ticket #{ticket_id} Escalated",
                "message": "Your ticket #{ticket_id} has been escalated to a senior team member for specialized attention."
            },
            "workflow_completed": {
                "title": "Workflow {workflow_id} Completed",
                "message": "Your workflow has completed successfully. Status: {status}"
            },
            "workflow_failed": {
                "title": "Workflow {workflow_id} Failed", 
                "message": "Your workflow encountered an error and could not complete. Status: {status}"
            },
            "workflow_cancelled": {
                "title": "Workflow {workflow_id} Cancelled",
                "message": "Your workflow has been cancelled. Status: {status}"
            }
        }
    
    def _get_ticket_notification_template(self, event_type: str) -> Dict[str, str]:
        """Get ticket notification template."""
        template_key = f"ticket_{event_type}"
        return self._templates.get(template_key, {
            "title": "Ticket Update",
            "message": "Your ticket has been updated."
        })
    
    def _get_workflow_notification_template(self, status: str) -> Dict[str, str]:
        """Get workflow notification template."""
        template_key = f"workflow_{status}"
        return self._templates.get(template_key, {
            "title": "Workflow Update",
            "message": "Your workflow status has changed."
        })

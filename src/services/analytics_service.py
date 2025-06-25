"""
Analytics Service for generating reports, metrics, and dashboard data.
Provides comprehensive analytics capabilities for the AI Ticket System.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from core.base_service import BaseService
from data.models.ticket import Ticket, TicketStatus, TicketPriority
from data.models.user import User
from data.repositories.ticket_repository import TicketRepository
from data.repositories.user_repository import UserRepository
from utils.exceptions import ServiceError, ValidationError
from config.settings import Settings


class MetricType(Enum):
    """Types of metrics available for analytics."""
    TICKET_METRICS = "ticket_metrics"
    USER_METRICS = "user_metrics"
    PERFORMANCE_METRICS = "performance_metrics"
    RESOLUTION_METRICS = "resolution_metrics"
    TREND_METRICS = "trend_metrics"


class ReportFormat(Enum):
    """Available report formats."""
    JSON = "json"
    CSV = "csv"
    SUMMARY = "summary"


@dataclass
class TicketMetrics:
    """Data structure for ticket-related metrics."""
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    in_progress_tickets: int
    high_priority_tickets: int
    medium_priority_tickets: int
    low_priority_tickets: int
    avg_resolution_time_hours: float
    tickets_by_status: Dict[str, int]
    tickets_by_priority: Dict[str, int]


@dataclass
class UserMetrics:
    """Data structure for user-related metrics."""
    total_users: int
    active_users: int
    users_by_role: Dict[str, int]
    avg_tickets_per_user: float
    top_ticket_creators: List[Dict[str, Any]]


@dataclass
class PerformanceMetrics:
    """Data structure for system performance metrics."""
    avg_response_time_seconds: float
    total_agent_calls: int
    successful_resolutions: int
    escalation_rate: float
    user_satisfaction_score: float


@dataclass
class TrendData:
    """Data structure for trend analysis."""
    period: str
    ticket_volume: List[Tuple[str, int]]
    resolution_trends: List[Tuple[str, float]]
    user_activity: List[Tuple[str, int]]


class AnalyticsService(BaseService):
    """
    Service for generating analytics, reports, and dashboard data.
    
    Provides comprehensive analytics capabilities including:
    - Ticket analytics and trends
    - User activity metrics
    - System performance metrics
    - Custom report generation
    - Dashboard data aggregation
    """

    def __init__(self, ticket_repository: TicketRepository, user_repository: UserRepository, settings: Settings):
        """
        Initialize the AnalyticsService.
        
        Args:
            ticket_repository: Repository for ticket data access
            user_repository: Repository for user data access
            settings: Application settings
        """
        super().__init__(settings)
        self.ticket_repository = ticket_repository
        self.user_repository = user_repository
        self.logger = logging.getLogger(__name__)

    def get_service_name(self) -> str:
        """Return the service name."""
        return "AnalyticsService"

    async def get_ticket_metrics(self, start_date: Optional[datetime] = None, 
                                end_date: Optional[datetime] = None) -> TicketMetrics:
        """
        Get comprehensive ticket metrics for a given time period.
        
        Args:
            start_date: Start date for metrics calculation (defaults to 30 days ago)
            end_date: End date for metrics calculation (defaults to now)
            
        Returns:
            TicketMetrics object with comprehensive ticket statistics
            
        Raises:
            ServiceError: If metrics calculation fails
        """
        try:
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Validate date range
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")

            self.logger.info(f"Calculating ticket metrics from {start_date} to {end_date}")

            # Get all tickets in the date range
            tickets = self.ticket_repository.get_tickets_by_date_range(start_date, end_date)
            
            total_tickets = len(tickets)
            
            # Count by status
            status_counts = {}
            for status in TicketStatus:
                status_counts[status.value] = sum(1 for t in tickets if t.status == status)
            
            # Count by priority
            priority_counts = {}
            for priority in TicketPriority:
                priority_counts[priority.value] = sum(1 for t in tickets if t.priority == priority)
            
            # Calculate resolution time
            resolved_tickets = [t for t in tickets if t.status == TicketStatus.CLOSED and t.resolved_at]
            avg_resolution_time = 0.0
            if resolved_tickets:
                total_resolution_time = sum(
                    (t.resolved_at - t.created_at).total_seconds() / 3600 
                    for t in resolved_tickets
                )
                avg_resolution_time = total_resolution_time / len(resolved_tickets)

            return TicketMetrics(
                total_tickets=total_tickets,
                open_tickets=status_counts.get(TicketStatus.OPEN.value, 0),
                closed_tickets=status_counts.get(TicketStatus.CLOSED.value, 0),
                in_progress_tickets=status_counts.get(TicketStatus.IN_PROGRESS.value, 0),
                high_priority_tickets=priority_counts.get(TicketPriority.HIGH.value, 0),
                medium_priority_tickets=priority_counts.get(TicketPriority.MEDIUM.value, 0),
                low_priority_tickets=priority_counts.get(TicketPriority.LOW.value, 0),
                avg_resolution_time_hours=avg_resolution_time,
                tickets_by_status=status_counts,
                tickets_by_priority=priority_counts
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate ticket metrics: {str(e)}")
            raise ServiceError(f"Failed to calculate ticket metrics: {str(e)}")

    async def get_user_metrics(self) -> UserMetrics:
        """
        Get comprehensive user metrics.
        
        Returns:
            UserMetrics object with user statistics
            
        Raises:
            ServiceError: If metrics calculation fails
        """
        try:
            self.logger.info("Calculating user metrics")

            users = self.user_repository.get_all_users()
            total_users = len(users)
            
            # Count active users (users who created tickets in last 30 days)
            recent_date = datetime.now() - timedelta(days=30)
            recent_tickets = self.ticket_repository.get_tickets_by_date_range(recent_date, datetime.now())
            active_user_ids = set(t.created_by for t in recent_tickets)
            active_users = len(active_user_ids)
            
            # Count by role (use actual role strings from database)
            role_counts = {}
            for user in users:
                role = user.role_in_company
                role_counts[role] = role_counts.get(role, 0) + 1
            
            # Calculate average tickets per user
            all_tickets = self.ticket_repository.get_all_tickets()
            avg_tickets_per_user = len(all_tickets) / total_users if total_users > 0 else 0
            
            # Get top ticket creators
            user_ticket_counts = {}
            for ticket in all_tickets:
                user_ticket_counts[ticket.created_by] = user_ticket_counts.get(ticket.created_by, 0) + 1
            
            top_creators = []
            for user_id, count in sorted(user_ticket_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                user = self.user_repository.get_by_id(user_id)
                if user:
                    top_creators.append({
                        "user_id": user_id,
                        "username": user.username,
                        "ticket_count": count
                    })

            return UserMetrics(
                total_users=total_users,
                active_users=active_users,
                users_by_role=role_counts,
                avg_tickets_per_user=avg_tickets_per_user,
                top_ticket_creators=top_creators
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate user metrics: {str(e)}")
            raise ServiceError(f"Failed to calculate user metrics: {str(e)}")

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get system performance metrics.
        
        Returns:
            PerformanceMetrics object with performance statistics
            
        Raises:
            ServiceError: If metrics calculation fails
        """
        try:
            self.logger.info("Calculating performance metrics")

            # Get recent tickets for performance analysis
            recent_date = datetime.now() - timedelta(days=7)
            recent_tickets = self.ticket_repository.get_tickets_by_date_range(recent_date, datetime.now())
            
            # Calculate average response time (simulated - would be based on actual response logs)
            avg_response_time = 2.5  # Placeholder - would be calculated from actual response time logs
            
            # Calculate total agent calls (simulated)
            total_agent_calls = len(recent_tickets) * 3  # Assuming average 3 agent calls per ticket
            
            # Calculate successful resolutions
            resolved_tickets = [t for t in recent_tickets if t.status == TicketStatus.CLOSED]
            successful_resolutions = len(resolved_tickets)
            
            # Calculate escalation rate
            escalated_tickets = [t for t in recent_tickets if t.priority == TicketPriority.HIGH]
            escalation_rate = len(escalated_tickets) / len(recent_tickets) * 100 if recent_tickets else 0
            
            # Calculate user satisfaction score (simulated)
            user_satisfaction = 4.2  # Placeholder - would be calculated from actual feedback
            
            return PerformanceMetrics(
                avg_response_time_seconds=avg_response_time,
                total_agent_calls=total_agent_calls,
                successful_resolutions=successful_resolutions,
                escalation_rate=escalation_rate,
                user_satisfaction_score=user_satisfaction
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {str(e)}")
            raise ServiceError(f"Failed to calculate performance metrics: {str(e)}")

    async def get_trend_data(self, days: int = 30) -> TrendData:
        """
        Get trend analysis data for the specified number of days.
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            TrendData object with trend analysis
            
        Raises:
            ServiceError: If trend calculation fails
        """
        try:
            self.logger.info(f"Calculating trend data for {days} days")

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get daily ticket volumes
            ticket_volume = []
            for i in range(days):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                day_tickets = self.ticket_repository.get_tickets_by_date_range(day_start, day_end)
                ticket_volume.append((day_start.strftime("%Y-%m-%d"), len(day_tickets)))
            
            # Calculate weekly resolution trends
            resolution_trends = []
            for week in range(0, days, 7):
                week_start = start_date + timedelta(days=week)
                week_end = week_start + timedelta(days=7)
                week_tickets = self.ticket_repository.get_tickets_by_date_range(week_start, week_end)
                resolved = [t for t in week_tickets if t.status == TicketStatus.CLOSED and t.resolved_at]
                
                if resolved:
                    avg_resolution = sum(
                        (t.resolved_at - t.created_at).total_seconds() / 3600 
                        for t in resolved
                    ) / len(resolved)
                else:
                    avg_resolution = 0
                
                resolution_trends.append((week_start.strftime("%Y-%m-%d"), avg_resolution))
            
            # Calculate user activity trends (placeholder)
            user_activity = []
            for week in range(0, days, 7):
                week_start = start_date + timedelta(days=week)
                # Simulated user activity - would be calculated from actual user activity logs
                activity_count = len(self.user_repository.get_all_users()) * 0.7  # Placeholder
                user_activity.append((week_start.strftime("%Y-%m-%d"), int(activity_count)))
            
            return TrendData(
                period=f"{days} days",
                ticket_volume=ticket_volume,
                resolution_trends=resolution_trends,
                user_activity=user_activity
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate trend data: {str(e)}")
            raise ServiceError(f"Failed to calculate trend data: {str(e)}")

    async def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard data.
        
        Returns:
            Dictionary containing all dashboard metrics and data
            
        Raises:
            ServiceError: If dashboard data generation fails
        """
        try:
            self.logger.info("Generating dashboard data")

            # Get all metrics
            ticket_metrics = await self.get_ticket_metrics()
            user_metrics = await self.get_user_metrics()
            performance_metrics = await self.get_performance_metrics()
            trend_data = await self.get_trend_data()

            return {
                "timestamp": datetime.now().isoformat(),
                "ticket_metrics": asdict(ticket_metrics),
                "user_metrics": asdict(user_metrics),
                "performance_metrics": asdict(performance_metrics),
                "trend_data": asdict(trend_data),
                "summary": {
                    "total_tickets": ticket_metrics.total_tickets,
                    "open_tickets": ticket_metrics.open_tickets,
                    "resolution_rate": (
                        ticket_metrics.closed_tickets / ticket_metrics.total_tickets * 100 
                        if ticket_metrics.total_tickets > 0 else 0
                    ),
                    "avg_resolution_hours": ticket_metrics.avg_resolution_time_hours,
                    "active_users": user_metrics.active_users,
                    "system_performance": performance_metrics.user_satisfaction_score
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to generate dashboard data: {str(e)}")
            raise ServiceError(f"Failed to generate dashboard data: {str(e)}")

    async def generate_custom_report(self, metric_types: List[MetricType], 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   report_format: ReportFormat = ReportFormat.JSON) -> Dict[str, Any]:
        """
        Generate a custom report with specified metrics.
        
        Args:
            metric_types: List of metric types to include
            start_date: Start date for the report
            end_date: End date for the report
            report_format: Format of the report output
            
        Returns:
            Custom report data
            
        Raises:
            ServiceError: If report generation fails
            ValidationError: If invalid parameters provided
        """
        try:
            if not metric_types:
                raise ValidationError("At least one metric type must be specified")

            self.logger.info(f"Generating custom report with metrics: {[m.value for m in metric_types]}")

            report_data = {
                "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "generated_at": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "format": report_format.value,
                "metrics": {}
            }

            # Generate requested metrics
            for metric_type in metric_types:
                if metric_type == MetricType.TICKET_METRICS:
                    report_data["metrics"]["tickets"] = asdict(
                        await self.get_ticket_metrics(start_date, end_date)
                    )
                elif metric_type == MetricType.USER_METRICS:
                    report_data["metrics"]["users"] = asdict(await self.get_user_metrics())
                elif metric_type == MetricType.PERFORMANCE_METRICS:
                    report_data["metrics"]["performance"] = asdict(await self.get_performance_metrics())
                elif metric_type == MetricType.TREND_METRICS:
                    days = 30
                    if start_date and end_date:
                        days = (end_date - start_date).days
                    report_data["metrics"]["trends"] = asdict(await self.get_trend_data(days))

            return report_data

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to generate custom report: {str(e)}")
            raise ServiceError(f"Failed to generate custom report: {str(e)}")

    async def get_real_time_stats(self) -> Dict[str, Any]:
        """
        Get real-time system statistics for live monitoring.
        
        Returns:
            Real-time statistics
            
        Raises:
            ServiceError: If statistics calculation fails
        """
        try:
            self.logger.info("Calculating real-time statistics")

            # Get current counts
            all_tickets = self.ticket_repository.get_all_tickets()
            all_users = self.user_repository.get_all_users()
            
            # Get today's activity
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_tickets = self.ticket_repository.get_tickets_by_date_range(today, datetime.now())
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "online",
                "counters": {
                    "total_tickets": len(all_tickets),
                    "open_tickets": len([t for t in all_tickets if t.status == TicketStatus.OPEN]),
                    "tickets_today": len(today_tickets),
                    "total_users": len(all_users),
                    "active_sessions": len(all_users)  # Placeholder - would track actual sessions
                },
                "performance": {
                    "avg_response_time_ms": 2500,  # Placeholder
                    "system_load": 0.65,  # Placeholder
                    "memory_usage_mb": 512  # Placeholder
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get real-time stats: {str(e)}")
            raise ServiceError(f"Failed to get real-time stats: {str(e)}")

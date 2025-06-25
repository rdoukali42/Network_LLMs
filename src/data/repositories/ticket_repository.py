"""
Ticket repository for data access operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from data.models.ticket import Ticket, TicketStatus, TicketPriority, TicketType
from core.base_repository import BaseRepository
from utils.exceptions import DatabaseError
import json


class TicketRepository(BaseRepository[Ticket]):
    """Repository for ticket data operations."""
    
    def __init__(self):
        super().__init__(
            db_path="data/databases/employees.db",
            table_name="tickets"
        )
    
    def create(self, ticket: Ticket) -> Ticket:
        """Create a new ticket."""
        try:
            query = """
                INSERT INTO tickets (
                    user_id, title, description, category, priority, 
                    status, assigned_agent, resolution, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            from data.database_manager import db_manager
            
            ticket_id = db_manager.execute_query(
                query,
                (
                    ticket.user_id,
                    ticket.title,
                    ticket.description,
                    ticket.ticket_type.value if ticket.ticket_type else "other",
                    ticket.priority.value if ticket.priority else "medium",
                    ticket.status.value if ticket.status else "open",
                    ticket.assigned_agent,
                    ticket.resolution,
                    ticket.created_at.isoformat() if ticket.created_at else datetime.now().isoformat(),
                    ticket.updated_at.isoformat() if ticket.updated_at else datetime.now().isoformat()
                )
            )
            
            if ticket_id:
                ticket.id = ticket_id
                self.logger.info(f"Created ticket {ticket_id}")
                return ticket
            else:
                raise DatabaseError("Failed to create ticket")
                
        except Exception as e:
            self.logger.error(f"Error creating ticket: {e}")
            raise DatabaseError(f"Failed to create ticket: {e}")
    
    def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ID."""
        try:
            from data.database_manager import db_manager
            
            query = "SELECT * FROM tickets WHERE id = ?"
            row = db_manager.execute_query(query, (ticket_id,), fetch="one")
            
            if row:
                return self._row_to_ticket(row)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting ticket {ticket_id}: {e}")
            raise DatabaseError(f"Failed to get ticket: {e}")
    
    def get_by_user_id(
        self, 
        user_id: int, 
        status: Optional[TicketStatus] = None,
        limit: int = 50
    ) -> List[Ticket]:
        """Get tickets by user ID."""
        try:
            from data.database_manager import db_manager
            
            if status:
                query = """
                    SELECT * FROM tickets 
                    WHERE user_id = ? AND status = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                rows = db_manager.execute_query(
                    query, 
                    (user_id, status.value, limit), 
                    fetch="all"
                )
            else:
                query = """
                    SELECT * FROM tickets 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                rows = db_manager.execute_query(
                    query, 
                    (user_id, limit), 
                    fetch="all"
                )
            
            return [self._row_to_ticket(row) for row in rows] if rows else []
            
        except Exception as e:
            self.logger.error(f"Error getting tickets for user {user_id}: {e}")
            raise DatabaseError(f"Failed to get tickets for user: {e}")
    
    def get_by_status(self, status: TicketStatus, limit: int = 100) -> List[Ticket]:
        """Get tickets by status."""
        try:
            from data.database_manager import db_manager
            
            query = """
                SELECT * FROM tickets 
                WHERE status = ? 
                ORDER BY priority DESC, created_at ASC 
                LIMIT ?
            """
            rows = db_manager.execute_query(
                query, 
                (status.value, limit), 
                fetch="all"
            )
            
            return [self._row_to_ticket(row) for row in rows] if rows else []
            
        except Exception as e:
            self.logger.error(f"Error getting tickets by status {status}: {e}")
            raise DatabaseError(f"Failed to get tickets by status: {e}")
    
    def get_tickets_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Ticket]:
        """Get tickets created within a date range."""
        try:
            from data.database_manager import db_manager
            
            query = """
                SELECT * FROM tickets 
                WHERE created_at >= ? AND created_at <= ?
                ORDER BY created_at DESC
            """
            rows = db_manager.execute_query(
                query, 
                (start_date.isoformat(), end_date.isoformat()), 
                fetch="all"
            )
            
            return [self._row_to_ticket(row) for row in rows] if rows else []
            
        except Exception as e:
            self.logger.error(f"Error getting tickets by date range: {e}")
            raise DatabaseError(f"Failed to get tickets by date range: {e}")
    
    def get_all_tickets(self) -> List[Ticket]:
        """Get all tickets in the system."""
        try:
            from data.database_manager import db_manager
            
            query = "SELECT * FROM tickets ORDER BY created_at DESC"
            rows = db_manager.execute_query(query, fetch="all")
            
            return [self._row_to_ticket(row) for row in rows] if rows else []
            
        except Exception as e:
            self.logger.error(f"Error getting all tickets: {e}")
            raise DatabaseError(f"Failed to get all tickets: {e}")
    
    def update(self, ticket: Ticket) -> Ticket:
        """Update an existing ticket."""
        try:
            from data.database_manager import db_manager
            
            query = """
                UPDATE tickets SET 
                    title = ?, description = ?, category = ?, priority = ?, 
                    status = ?, assigned_agent = ?, resolution = ?, 
                    updated_at = ?, resolved_at = ?
                WHERE id = ?
            """
            
            ticket.updated_at = datetime.now()
            
            db_manager.execute_query(
                query,
                (
                    ticket.title,
                    ticket.description,
                    ticket.ticket_type.value if ticket.ticket_type else "other",
                    ticket.priority.value if ticket.priority else "medium",
                    ticket.status.value if ticket.status else "open",
                    ticket.assigned_agent,
                    ticket.resolution,
                    ticket.updated_at.isoformat(),
                    ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                    ticket.id
                )
            )
            
            self.logger.info(f"Updated ticket {ticket.id}")
            return ticket
            
        except Exception as e:
            self.logger.error(f"Error updating ticket {ticket.id}: {e}")
            raise DatabaseError(f"Failed to update ticket: {e}")
    
    def delete(self, ticket_id: int) -> bool:
        """Delete a ticket (soft delete by setting status to cancelled)."""
        try:
            from data.database_manager import db_manager
            
            query = """
                UPDATE tickets SET 
                    status = 'cancelled', 
                    updated_at = ?
                WHERE id = ?
            """
            
            db_manager.execute_query(
                query,
                (datetime.now().isoformat(), ticket_id)
            )
            
            self.logger.info(f"Deleted (cancelled) ticket {ticket_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting ticket {ticket_id}: {e}")
            raise DatabaseError(f"Failed to delete ticket: {e}")
    
    def search(
        self, 
        query: str, 
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Ticket]:
        """Search tickets by title or description."""
        try:
            from data.database_manager import db_manager
            
            search_pattern = f"%{query}%"
            
            if user_id:
                sql_query = """
                    SELECT * FROM tickets 
                    WHERE (title LIKE ? OR description LIKE ?) AND user_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                rows = db_manager.execute_query(
                    sql_query,
                    (search_pattern, search_pattern, user_id, limit),
                    fetch="all"
                )
            else:
                sql_query = """
                    SELECT * FROM tickets 
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                rows = db_manager.execute_query(
                    sql_query,
                    (search_pattern, search_pattern, limit),
                    fetch="all"
                )
            
            return [self._row_to_ticket(row) for row in rows] if rows else []
            
        except Exception as e:
            self.logger.error(f"Error searching tickets: {e}")
            raise DatabaseError(f"Failed to search tickets: {e}")
    
    def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get ticket analytics for the specified time period."""
        try:
            from data.database_manager import db_manager
            
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Total tickets in period
            total_query = """
                SELECT COUNT(*) as total FROM tickets 
                WHERE created_at >= ?
            """
            total_result = db_manager.execute_query(total_query, (start_date,), fetch="one")
            total_tickets = total_result[0] if total_result else 0
            
            # Status distribution
            status_query = """
                SELECT status, COUNT(*) as count FROM tickets 
                WHERE created_at >= ?
                GROUP BY status
            """
            status_rows = db_manager.execute_query(status_query, (start_date,), fetch="all")
            status_distribution = {row[0]: row[1] for row in status_rows} if status_rows else {}
            
            # Priority distribution
            priority_query = """
                SELECT priority, COUNT(*) as count FROM tickets 
                WHERE created_at >= ?
                GROUP BY priority
            """
            priority_rows = db_manager.execute_query(priority_query, (start_date,), fetch="all")
            priority_distribution = {row[0]: row[1] for row in priority_rows} if priority_rows else {}
            
            # Average resolution time
            resolution_query = """
                SELECT AVG(
                    CASE 
                        WHEN resolved_at IS NOT NULL 
                        THEN julianday(resolved_at) - julianday(created_at)
                        ELSE NULL 
                    END
                ) as avg_days FROM tickets 
                WHERE created_at >= ? AND resolved_at IS NOT NULL
            """
            resolution_result = db_manager.execute_query(resolution_query, (start_date,), fetch="one")
            avg_resolution_days = resolution_result[0] if resolution_result and resolution_result[0] else 0
            
            return {
                "period_days": days,
                "total_tickets": total_tickets,
                "status_distribution": status_distribution,
                "priority_distribution": priority_distribution,
                "average_resolution_days": round(avg_resolution_days, 2) if avg_resolution_days else 0,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ticket analytics: {e}")
            raise DatabaseError(f"Failed to get ticket analytics: {e}")
    
    def _initialize_table(self):
        """Initialize the tickets table schema."""
        # This is handled by the database manager
        pass
    
    def _entity_to_dict(self, entity: Ticket) -> Dict[str, Any]:
        """Convert ticket entity to dictionary."""
        return entity.to_dict()
    
    def _row_to_entity(self, row) -> Ticket:
        """Convert database row to Ticket entity."""
        return self._row_to_ticket(row)
    
    def _row_to_ticket(self, row) -> Ticket:
        """Convert database row to Ticket object."""
        try:
            # Handle ticket type conversion
            ticket_type_value = row["category"] if "category" in row.keys() else "other"
            try:
                ticket_type = TicketType(ticket_type_value)
            except ValueError:
                ticket_type = TicketType.OTHER
            
            # Handle priority conversion
            priority_value = row["priority"] if "priority" in row.keys() else "medium"
            try:
                priority = TicketPriority(priority_value)
            except ValueError:
                priority = TicketPriority.MEDIUM
            
            # Handle status conversion
            status_value = row["status"] if "status" in row.keys() else "open"
            try:
                status = TicketStatus(status_value)
            except ValueError:
                status = TicketStatus.OPEN
            
            # Parse datetime fields
            created_at = None
            if row["created_at"]:
                try:
                    created_at = datetime.fromisoformat(row["created_at"])
                except ValueError:
                    created_at = datetime.now()
            
            updated_at = None
            if row["updated_at"]:
                try:
                    updated_at = datetime.fromisoformat(row["updated_at"])
                except ValueError:
                    updated_at = datetime.now()
            
            resolved_at = None
            if row["resolved_at"]:
                try:
                    resolved_at = datetime.fromisoformat(row["resolved_at"])
                except ValueError:
                    resolved_at = None
            
            return Ticket(
                id=row["id"],
                user_id=row["user_id"],
                title=row["title"] or "",
                description=row["description"] or "",
                ticket_type=ticket_type,
                priority=priority,
                status=status,
                assigned_agent=row["assigned_agent"],
                resolution=row["resolution"],
                created_at=created_at,
                updated_at=updated_at,
                resolved_at=resolved_at
            )
            
        except Exception as e:
            self.logger.error(f"Error converting row to ticket: {e}")
            raise DatabaseError(f"Failed to convert database row to ticket: {e}")

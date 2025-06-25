"""
User repository for data access operations.
"""

from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime

from core.base_repository import BaseRepository
from data.models.user import User, AvailabilityStatus
from utils.exceptions import DatabaseError
from utils.constants import DEFAULT_DATABASE_PATH


class UserRepository(BaseRepository[User]):
    """Repository for user data access operations."""
    
    def __init__(self, db_path: str = DEFAULT_DATABASE_PATH):
        super().__init__(db_path, "employees_data_table")
        self.logger.debug(f"[DEBUG] UserRepository initializing with db_path: {db_path}")
        self.logger.debug(f"[DEBUG] UserRepository DEFAULT_DATABASE_PATH: {DEFAULT_DATABASE_PATH}")
        
        # Debug: Test immediate connection and count
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM employees_data_table")
                count = cursor.fetchone()[0]
                self.logger.debug(f"[DEBUG] UserRepository connected to {db_path}, found {count} users")
        except Exception as e:
            self.logger.error(f"[DEBUG] UserRepository connection test failed for {db_path}: {e}")
    
    def _initialize_table(self):
        """Initialize the users table schema."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS employees_data_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            role_in_company VARCHAR(100) NOT NULL,
            job_description TEXT NOT NULL,
            expertise TEXT NOT NULL,
            responsibilities TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            availability_status TEXT DEFAULT 'Offline',
            status_until TIMESTAMP NULL,
            last_seen TIMESTAMP NULL
        )
        """
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_username ON employees_data_table(username)",
            "CREATE INDEX IF NOT EXISTS idx_role ON employees_data_table(role_in_company)",
            "CREATE INDEX IF NOT EXISTS idx_active ON employees_data_table(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_availability ON employees_data_table(availability_status)"
        ]
        
        try:
            with self.get_connection() as conn:
                conn.execute(create_table_query)
                for index_query in indexes:
                    conn.execute(index_query)
                conn.commit()
                
            self.logger.info("User table initialized successfully")
        except Exception as e:
            raise DatabaseError(f"Failed to initialize user table: {e}", "create_table")
    
    def _row_to_entity(self, row: sqlite3.Row) -> User:
        """Convert database row to User entity."""
        try:
            # Parse datetime fields
            created_at = None
            if row['created_at']:
                try:
                    created_at = datetime.fromisoformat(row['created_at'])
                except ValueError:
                    # Handle different datetime formats
                    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
            
            updated_at = None
            if row['updated_at']:
                try:
                    updated_at = datetime.fromisoformat(row['updated_at'])
                except ValueError:
                    updated_at = datetime.strptime(row['updated_at'], '%Y-%m-%d %H:%M:%S')
            
            status_until = None
            if row['status_until']:
                try:
                    status_until = datetime.fromisoformat(row['status_until'])
                except ValueError:
                    status_until = datetime.strptime(row['status_until'], '%Y-%m-%d %H:%M:%S')
            
            last_seen = None
            if row['last_seen']:
                try:
                    last_seen = datetime.fromisoformat(row['last_seen'])
                except ValueError:
                    last_seen = datetime.strptime(row['last_seen'], '%Y-%m-%d %H:%M:%S')
            
            # Parse availability status
            availability_status = AvailabilityStatus.OFFLINE
            if row['availability_status']:
                try:
                    availability_status = AvailabilityStatus(row['availability_status'])
                except ValueError:
                    # Handle legacy status values
                    status_map = {
                        'Online': AvailabilityStatus.ONLINE,
                        'Offline': AvailabilityStatus.OFFLINE,
                        'Busy': AvailabilityStatus.BUSY,
                        'Away': AvailabilityStatus.AWAY
                    }
                    availability_status = status_map.get(row['availability_status'], AvailabilityStatus.OFFLINE)
            
            return User(
                id=row['id'],
                username=row['username'],
                full_name=row['full_name'],
                role_in_company=row['role_in_company'],
                job_description=row['job_description'],
                expertise=row['expertise'] or '',
                responsibilities=row['responsibilities'] or '',
                created_at=created_at,
                updated_at=updated_at,
                is_active=bool(row['is_active']),
                availability_status=availability_status,
                status_until=status_until,
                last_seen=last_seen
            )
        except Exception as e:
            self.logger.error(f"Failed to convert row to User entity: {e}")
            raise DatabaseError(f"Failed to convert database row to User: {e}")
    
    def _entity_to_dict(self, entity: User) -> Dict[str, Any]:
        """Convert User entity to dictionary for database operations."""
        return {
            'username': entity.username,
            'full_name': entity.full_name,
            'role_in_company': entity.role_in_company,
            'job_description': entity.job_description,
            'expertise': entity.expertise,
            'responsibilities': entity.responsibilities,
            'created_at': entity.created_at.isoformat() if entity.created_at else None,
            'updated_at': entity.updated_at.isoformat() if entity.updated_at else None,
            'is_active': entity.is_active,
            'availability_status': entity.availability_status.value,
            'status_until': entity.status_until.isoformat() if entity.status_until else None,
            'last_seen': entity.last_seen.isoformat() if entity.last_seen else None
        }
    
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User entity or None if not found
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE username = ?"
            results = self.execute_query(query, (username,))
            
            if results:
                return self._row_to_entity(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Failed to find user by username '{username}': {e}")
            raise DatabaseError(f"Failed to find user by username: {e}", "select", self.table_name)
    
    def find_by_role(self, role: str, limit: Optional[int] = None) -> List[User]:
        """
        Find users by role.
        
        Args:
            role: Role to search for
            limit: Maximum number of users to return
            
        Returns:
            List of User entities
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE role_in_company = ?"
            params = [role]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            results = self.execute_query(query, tuple(params))
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to find users by role '{role}': {e}")
            raise DatabaseError(f"Failed to find users by role: {e}", "select", self.table_name)
    
    def find_available_users(self, exclude_statuses: Optional[List[AvailabilityStatus]] = None) -> List[User]:
        """
        Find users who are currently available.
        
        Args:
            exclude_statuses: Statuses to exclude from results
            
        Returns:
            List of available User entities
        """
        try:
            # Default exclusions
            if exclude_statuses is None:
                exclude_statuses = [AvailabilityStatus.OFFLINE, AvailabilityStatus.DO_NOT_DISTURB]
            
            # Build query
            exclude_values = [status.value for status in exclude_statuses]
            placeholders = ','.join(['?' for _ in exclude_values])
            
            query = f"""
            SELECT * FROM {self.table_name} 
            WHERE is_active = 1 
            AND availability_status NOT IN ({placeholders})
            AND (status_until IS NULL OR status_until <= CURRENT_TIMESTAMP)
            ORDER BY last_seen DESC
            """
            
            results = self.execute_query(query, tuple(exclude_values))
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to find available users: {e}")
            raise DatabaseError(f"Failed to find available users: {e}", "select", self.table_name)
    
    def find_by_expertise(self, expertise_keyword: str, limit: Optional[int] = None) -> List[User]:
        """
        Find users by expertise keyword.
        
        Args:
            expertise_keyword: Keyword to search in expertise field
            limit: Maximum number of users to return
            
        Returns:
            List of User entities with matching expertise
        """
        try:
            query = f"""
            SELECT * FROM {self.table_name} 
            WHERE is_active = 1 
            AND (expertise LIKE ? OR responsibilities LIKE ?)
            ORDER BY full_name
            """
            
            search_term = f"%{expertise_keyword}%"
            params = [search_term, search_term]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            results = self.execute_query(query, tuple(params))
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to find users by expertise '{expertise_keyword}': {e}")
            raise DatabaseError(f"Failed to find users by expertise: {e}", "select", self.table_name)
    
    def update_availability(self, username: str, status: AvailabilityStatus, 
                          until: Optional[datetime] = None) -> Optional[User]:
        """
        Update user availability status.
        
        Args:
            username: Username of the user
            status: New availability status
            until: Optional end time for the status
            
        Returns:
            Updated User entity or None if user not found
        """
        try:
            updates = {
                'availability_status': status.value,
                'status_until': until.isoformat() if until else None,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Find user first to get ID
            user = self.find_by_username(username)
            if not user:
                return None
            
            return self.update(user.id, updates)
        except Exception as e:
            self.logger.error(f"Failed to update availability for user '{username}': {e}")
            raise DatabaseError(f"Failed to update user availability: {e}", "update", self.table_name)
    
    def update_last_seen(self, username: str) -> Optional[User]:
        """
        Update user's last seen timestamp.
        
        Args:
            username: Username of the user
            
        Returns:
            Updated User entity or None if user not found
        """
        try:
            updates = {
                'last_seen': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Find user first to get ID
            user = self.find_by_username(username)
            if not user:
                return None
            
            return self.update(user.id, updates)
        except Exception as e:
            self.logger.error(f"Failed to update last seen for user '{username}': {e}")
            raise DatabaseError(f"Failed to update user last seen: {e}", "update", self.table_name)
    
    def get_active_users(self) -> List[User]:
        """
        Get all active users.
        
        Returns:
            List of active User entities
        """
        return self.find_by_criteria({'is_active': True})
    
    def deactivate_user(self, username: str) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            username: Username of the user to deactivate
            
        Returns:
            Updated User entity or None if user not found
        """
        try:
            updates = {
                'is_active': False,
                'availability_status': AvailabilityStatus.OFFLINE.value,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Find user first to get ID
            user = self.find_by_username(username)
            if not user:
                return None
            
            return self.update(user.id, updates)
        except Exception as e:
            self.logger.error(f"Failed to deactivate user '{username}': {e}")
            raise DatabaseError(f"Failed to deactivate user: {e}", "update", self.table_name)
    
    def search_users(self, search_term: str, limit: Optional[int] = None) -> List[User]:
        """
        Search for users by username, full name, or role.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of users to return
            
        Returns:
            List of matching User entities
        """
        try:
            search_pattern = f"%{search_term}%"
            query = f"""
            SELECT * FROM {self.table_name} 
            WHERE is_active = 1 
            AND (username LIKE ? OR full_name LIKE ? OR role_in_company LIKE ?)
            ORDER BY full_name
            """
            
            params = [search_pattern, search_pattern, search_pattern]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            results = self.execute_query(query, tuple(params))
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to search users with term '{search_term}': {e}")
            raise DatabaseError(f"Failed to search users: {e}", "select", self.table_name)
    
    def get_all_users(self) -> List[User]:
        """
        Get all users in the system.
        
        Returns:
            List of all User entities
        """
        try:
            query = f"SELECT * FROM {self.table_name} ORDER BY full_name"
            results = self.execute_query(query)
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Failed to get all users: {e}")
            raise DatabaseError(f"Failed to get all users: {e}", "select", self.table_name)
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = ?"
            
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (user_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                    
                return self._row_to_entity(row)
                
        except Exception as e:
            self.logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        self.logger.debug(f"[DEBUG] UserRepository.get_by_username called for '{username}' using db_path: {self.db_path}")
        try:
            query = f"SELECT * FROM {self.table_name} WHERE username = ?"
            
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                
                if not row:
                    self.logger.debug(f"[DEBUG] UserRepository.get_by_username: No user found for '{username}' in {self.db_path}")
                    return None
                    
                user = self._row_to_entity(row)
                self.logger.debug(f"[DEBUG] UserRepository.get_by_username: Found user '{username}' -> {user.full_name}")
                return user
                
        except Exception as e:
            self.logger.error(f"[DEBUG] UserRepository.get_by_username failed for '{username}' in {self.db_path}: {e}")
            return None

"""
Base repository class providing common data access patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
from utils.logging_config import get_logger
from utils.exceptions import DatabaseError, ValidationError
import sqlite3
from pathlib import Path


T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base class for all repositories in the system.
    
    Provides common database operations and patterns for data access.
    """
    
    def __init__(self, db_path: str, table_name: str):
        """Initialize the base repository."""
        self.db_path = db_path
        self.table_name = table_name
        self.logger = get_logger(f"repository.{table_name}")
        
        # Ensure database file exists
        self._ensure_database_exists()
        
        # Initialize table if needed
        self._initialize_table()
    
    def _ensure_database_exists(self):
        """Ensure the database file and directory exist."""
        try:
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create database file if it doesn't exist
            if not db_file.exists():
                self.logger.info(f"Creating database file: {self.db_path}")
                with sqlite3.connect(self.db_path) as conn:
                    # Enable foreign key constraints
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.commit()
                    
        except Exception as e:
            raise DatabaseError(f"Failed to ensure database exists: {e}", "create_database")
    
    @abstractmethod
    def _initialize_table(self):
        """Initialize the table schema. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _row_to_entity(self, row: sqlite3.Row) -> T:
        """Convert database row to entity object. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity object to dictionary. Must be implemented by subclasses."""
        pass
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}", "connection")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of query results
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Query execution failed: {query}, params: {params}, error: {e}")
            raise DatabaseError(f"Query execution failed: {e}", "select", self.table_name)
    
    def execute_command(self, command: str, params: tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE command.
        
        Args:
            command: SQL command string
            params: Command parameters
            
        Returns:
            Number of affected rows
            
        Raises:
            DatabaseError: If command execution fails
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(command, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Command execution failed: {command}, params: {params}, error: {e}")
            raise DatabaseError(f"Command execution failed: {e}", "modify", self.table_name)
    
    def find_by_id(self, entity_id: Union[str, int]) -> Optional[T]:
        """
        Find entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity object or None if not found
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = ?"
            results = self.execute_query(query, (entity_id,))
            
            if results:
                return self._row_to_entity(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Find by ID failed for {entity_id}: {e}")
            raise DatabaseError(f"Failed to find entity by ID: {e}", "select", self.table_name)
    
    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        Find all entities with optional pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entity objects
        """
        try:
            query = f"SELECT * FROM {self.table_name}"
            params = []
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params = [limit, offset]
            
            results = self.execute_query(query, tuple(params))
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Find all failed: {e}")
            raise DatabaseError(f"Failed to find all entities: {e}", "select", self.table_name)
    
    def find_by_criteria(self, criteria: Dict[str, Any], limit: Optional[int] = None) -> List[T]:
        """
        Find entities by criteria.
        
        Args:
            criteria: Search criteria as key-value pairs
            limit: Maximum number of entities to return
            
        Returns:
            List of matching entity objects
        """
        try:
            if not criteria:
                return self.find_all(limit=limit)
            
            # Build WHERE clause
            where_clauses = []
            params = []
            
            for key, value in criteria.items():
                where_clauses.append(f"{key} = ?")
                params.append(value)
            
            query = f"SELECT * FROM {self.table_name} WHERE {' AND '.join(where_clauses)}"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            results = self.execute_query(query, tuple(params))
            return [self._row_to_entity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Find by criteria failed: {e}")
            raise DatabaseError(f"Failed to find entities by criteria: {e}", "select", self.table_name)
    
    def create(self, entity: T) -> T:
        """
        Create a new entity.
        
        Args:
            entity: Entity object to create
            
        Returns:
            Created entity with generated ID
            
        Raises:
            DatabaseError: If creation fails
        """
        try:
            entity_dict = self._entity_to_dict(entity)
            
            # Remove ID if present (will be auto-generated)
            entity_dict.pop('id', None)
            
            if not entity_dict:
                raise ValidationError("Entity data is empty")
            
            # Build INSERT query
            columns = list(entity_dict.keys())
            placeholders = ['?' for _ in columns]
            values = [entity_dict[col] for col in columns]
            
            query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            with self.get_connection() as conn:
                cursor = conn.execute(query, values)
                conn.commit()
                entity_id = cursor.lastrowid
            
            # Return the created entity
            return self.find_by_id(entity_id)
        except Exception as e:
            self.logger.error(f"Create failed: {e}")
            raise DatabaseError(f"Failed to create entity: {e}", "insert", self.table_name)
    
    def update(self, entity_id: Union[str, int], updates: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing entity.
        
        Args:
            entity_id: Entity identifier
            updates: Fields to update
            
        Returns:
            Updated entity or None if not found
            
        Raises:
            DatabaseError: If update fails
        """
        try:
            if not updates:
                return self.find_by_id(entity_id)
            
            # Build UPDATE query
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            params.append(entity_id)
            
            query = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = ?"
            
            affected_rows = self.execute_command(query, tuple(params))
            
            if affected_rows > 0:
                return self.find_by_id(entity_id)
            return None
        except Exception as e:
            self.logger.error(f"Update failed for {entity_id}: {e}")
            raise DatabaseError(f"Failed to update entity: {e}", "update", self.table_name)
    
    def delete(self, entity_id: Union[str, int]) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            affected_rows = self.execute_command(query, (entity_id,))
            return affected_rows > 0
        except Exception as e:
            self.logger.error(f"Delete failed for {entity_id}: {e}")
            raise DatabaseError(f"Failed to delete entity: {e}", "delete", self.table_name)
    
    def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching criteria.
        
        Args:
            criteria: Optional search criteria
            
        Returns:
            Number of matching entities
        """
        try:
            if criteria:
                where_clauses = []
                params = []
                
                for key, value in criteria.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                
                query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {' AND '.join(where_clauses)}"
                results = self.execute_query(query, tuple(params))
            else:
                query = f"SELECT COUNT(*) FROM {self.table_name}"
                results = self.execute_query(query)
            
            return results[0][0] if results else 0
        except Exception as e:
            self.logger.error(f"Count failed: {e}")
            raise DatabaseError(f"Failed to count entities: {e}", "select", self.table_name)
    
    def exists(self, entity_id: Union[str, int]) -> bool:
        """
        Check if entity exists by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if entity exists, False otherwise
        """
        try:
            query = f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1"
            results = self.execute_query(query, (entity_id,))
            return len(results) > 0
        except Exception as e:
            self.logger.error(f"Exists check failed for {entity_id}: {e}")
            raise DatabaseError(f"Failed to check entity existence: {e}", "select", self.table_name)

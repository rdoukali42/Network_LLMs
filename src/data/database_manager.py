"""
Database manager for centralized database operations.
"""

import sqlite3
import threading
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from config.settings import settings
from utils.logging_config import get_logger
from utils.exceptions import DatabaseError


class DatabaseManager:
    """
    Centralized database management with connection pooling and error handling.
    """
    
    def __init__(self):
        self.logger = get_logger("database.manager")
        self._connections: Dict[str, sqlite3.Connection] = {}
        self._locks: Dict[str, threading.Lock] = {}
        
        # Initialize databases
        self._initialize_databases()
    
    def _initialize_databases(self):
        """Initialize database connections and ensure tables exist."""
        try:
            # Ensure database directories exist
            for db_path in [settings.database.employees_db_path]:
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize main database
            self._ensure_database_schema()
            
            self.logger.info("Database manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database manager: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    def _ensure_database_schema(self):
        """Ensure all required tables exist with proper schema."""
        schema_queries = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                department TEXT,
                role TEXT DEFAULT 'employee',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Tickets table
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                assigned_agent TEXT,
                resolution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            # Conversations table
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,  -- 'user' or 'agent'
                sender_id TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,  -- JSON for additional data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
            """,
            
            # Workflow states table
            """
            CREATE TABLE IF NOT EXISTS workflow_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                current_state TEXT NOT NULL,
                previous_state TEXT,
                context_data TEXT,  -- JSON for state data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
            """,
            
            # Agent interactions table
            """
            CREATE TABLE IF NOT EXISTS agent_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                input_data TEXT,  -- JSON
                output_data TEXT,  -- JSON
                duration_ms INTEGER,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
            """,
            
            # Create indexes for better performance
            "CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets (user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_ticket_id ON conversations (ticket_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_states_ticket_id ON workflow_states (ticket_id)",
            "CREATE INDEX IF NOT EXISTS idx_agent_interactions_ticket_id ON agent_interactions (ticket_id)",
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for query in schema_queries:
                cursor.execute(query)
            conn.commit()
    
    @contextmanager
    def get_connection(self, db_name: str = "main"):
        """Get a database connection with proper error handling."""
        db_path = self._get_db_path(db_name)
        
        # Ensure lock exists for this database
        if db_name not in self._locks:
            self._locks[db_name] = threading.Lock()
        
        with self._locks[db_name]:
            try:
                # Create new connection for each request to avoid threading issues
                conn = sqlite3.connect(
                    db_path,
                    timeout=settings.database.connection_timeout,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row  # Enable column access by name
                
                yield conn
                
            except sqlite3.Error as e:
                self.logger.error(f"Database error: {e}")
                raise DatabaseError(f"Database operation failed: {e}")
            finally:
                if 'conn' in locals():
                    conn.close()
    
    def _get_db_path(self, db_name: str) -> str:
        """Get the file path for a database."""
        if db_name == "main":
            return settings.database.employees_db_path
        else:
            return f"data/databases/{db_name}.db"
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None, 
        fetch: str = "none",
        db_name: str = "main"
    ) -> Union[List[sqlite3.Row], sqlite3.Row, None]:
        """
        Execute a database query with proper error handling.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: 'one', 'all', or 'none'
            db_name: Database name to use
            
        Returns:
            Query results based on fetch parameter
        """
        try:
            with self.get_connection(db_name) as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch == "one":
                    return cursor.fetchone()
                elif fetch == "all":
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.lastrowid if query.strip().upper().startswith("INSERT") else None
                    
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    def backup_database(self, db_name: str = "main") -> str:
        """Create a backup of the specified database."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{db_name}_backup_{timestamp}.db"
        backup_path = Path(settings.database.backup_path) / backup_filename
        
        try:
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup
            with self.get_connection(db_name) as source_conn:
                backup_conn = sqlite3.connect(str(backup_path))
                source_conn.backup(backup_conn)
                backup_conn.close()
            
            self.logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            raise DatabaseError(f"Database backup failed: {e}")
    
    def get_table_info(self, table_name: str, db_name: str = "main") -> List[Dict[str, Any]]:
        """Get information about a table's structure."""
        query = f"PRAGMA table_info({table_name})"
        rows = self.execute_query(query, fetch="all", db_name=db_name)
        
        return [
            {
                "column_id": row[0],
                "name": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "default_value": row[4],
                "primary_key": bool(row[5])
            }
            for row in rows
        ] if rows else []
    
    def check_health(self) -> Dict[str, Any]:
        """Check database health and return status information."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check basic connectivity
                cursor.execute("SELECT 1")
                
                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                size_result = cursor.fetchone()
                db_size = size_result[0] if size_result else 0
                
                # Get table counts
                tables = ["users", "tickets", "conversations", "workflow_states", "agent_interactions"]
                table_counts = {}
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        table_counts[table] = cursor.fetchone()[0]
                    except sqlite3.Error:
                        table_counts[table] = "N/A"
                
                return {
                    "status": "healthy",
                    "database_size_bytes": db_size,
                    "table_counts": table_counts,
                    "last_checked": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


# Global database manager instance
db_manager = DatabaseManager()

"""
Database manager for employee data.
Handles SQLite database operations for employee registration and management.
"""

import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json


class DatabaseManager:
    """Manages SQLite database operations for employee data."""
    
    def __init__(self):
        """Initialize database manager and ensure database exists."""
        # Database path in data folder
        project_root = Path(__file__).parent.parent
        self.db_path = project_root / "data" / "databases" / "employees.db"
        self.backup_dir = project_root / "data" / "backups"
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_username ON employees_data_table(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_role ON employees_data_table(role_in_company)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_active ON employees_data_table(is_active)")
            
            conn.commit()
            print("✅ Employee database initialized")
    
    def create_employee(self, username: str, full_name: str, role_in_company: str, 
                       job_description: str, expertise: str, responsibilities: str) -> Tuple[bool, str]:
        """
        Create a new employee record.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if username already exists
                cursor = conn.execute(
                    "SELECT username FROM employees_data_table WHERE username = ?", 
                    (username,)
                )
                if cursor.fetchone():
                    return False, f"Username '{username}' already exists"
                
                # Insert new employee
                conn.execute("""
                    INSERT INTO employees_data_table 
                    (username, full_name, role_in_company, job_description, expertise, responsibilities)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, full_name, role_in_company, job_description, expertise, responsibilities))
                
                conn.commit()
                return True, f"Employee '{full_name}' registered successfully"
                
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_employee_by_username(self, username: str) -> Optional[Dict]:
        """Get employee by username."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.execute("""
                    SELECT * FROM employees_data_table 
                    WHERE username = ? AND is_active = TRUE
                """, (username,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    
    def get_all_employees(self, active_only: bool = True) -> List[Dict]:
        """Get all employees."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM employees_data_table"
                if active_only:
                    query += " WHERE is_active = TRUE"
                query += " ORDER BY created_at DESC"
                
                cursor = conn.execute(query)
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def get_employees_by_role(self, role: str) -> List[Dict]:
        """Get employees by role."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM employees_data_table 
                    WHERE role_in_company LIKE ? AND is_active = TRUE
                    ORDER BY full_name
                """, (f"%{role}%",))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def get_employees_by_expertise(self, expertise: str) -> List[Dict]:
        """Get employees by expertise."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM employees_data_table 
                    WHERE expertise LIKE ? AND is_active = TRUE
                    ORDER BY full_name
                """, (f"%{expertise}%",))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def update_employee(self, username: str, **kwargs) -> Tuple[bool, str]:
        """Update employee information."""
        try:
            # Valid fields that can be updated
            valid_fields = {
                'full_name', 'role_in_company', 'job_description', 
                'expertise', 'responsibilities', 'is_active'
            }
            
            # Filter valid fields
            update_fields = {k: v for k, v in kwargs.items() if k in valid_fields}
            
            if not update_fields:
                return False, "No valid fields to update"
            
            # Add updated_at timestamp
            update_fields['updated_at'] = datetime.now().isoformat()
            
            # Build SQL query
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values()) + [username]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"""
                    UPDATE employees_data_table 
                    SET {set_clause}
                    WHERE username = ?
                """, values)
                
                if cursor.rowcount == 0:
                    return False, f"Employee '{username}' not found"
                
                conn.commit()
                return True, f"Employee '{username}' updated successfully"
                
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def deactivate_employee(self, username: str) -> Tuple[bool, str]:
        """Deactivate an employee (soft delete)."""
        return self.update_employee(username, is_active=False)
    
    def get_employee_stats(self) -> Dict:
        """Get employee statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total employees
                cursor = conn.execute("SELECT COUNT(*) FROM employees_data_table WHERE is_active = TRUE")
                total_active = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM employees_data_table")
                total_all = cursor.fetchone()[0]
                
                # Role distribution
                cursor = conn.execute("""
                    SELECT role_in_company, COUNT(*) as count 
                    FROM employees_data_table 
                    WHERE is_active = TRUE 
                    GROUP BY role_in_company 
                    ORDER BY count DESC
                """)
                role_distribution = dict(cursor.fetchall())
                
                return {
                    "total_active": total_active,
                    "total_all": total_all,
                    "role_distribution": role_distribution,
                    "database_path": str(self.db_path)
                }
                
        except sqlite3.Error as e:
            return {"error": f"Database error: {str(e)}"}
    
    def backup_database(self) -> Tuple[bool, str]:
        """Create a backup of the database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"employees_backup_{timestamp}.db"
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            return True, f"Database backed up to {backup_path}"
            
        except Exception as e:
            return False, f"Backup failed: {str(e)}"
    
    def search_employees(self, search_term: str) -> List[Dict]:
        """Search employees by name, role, or expertise."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM employees_data_table 
                    WHERE is_active = TRUE AND (
                        full_name LIKE ? OR 
                        role_in_company LIKE ? OR 
                        expertise LIKE ? OR
                        responsibilities LIKE ?
                    )
                    ORDER BY full_name
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []


# Singleton instance for easy access
db_manager = DatabaseManager()

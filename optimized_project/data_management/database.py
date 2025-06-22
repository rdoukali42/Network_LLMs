"""
Database manager for employee data.
Handles SQLite database operations for employee registration and management.
This version is refactored for the optimized_project.
"""

import sqlite3
# import hashlib # Not used by core methods being kept
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import shutil # For backup_database

class DatabaseManager:
    """Manages SQLite database operations for employee data."""

    def __init__(self, project_root_path: Path):
        """
        Initialize database manager and ensure database exists.
        Args:
            project_root_path: The absolute path to the 'optimized_project' root.
        """
        self.project_root = project_root_path
        # Database path within optimized_project/data/databases/
        self.db_path = self.project_root / "data" / "databases" / "employees.db"
        self.backup_dir = self.project_root / "data" / "backups"

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

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
                    availability_status TEXT DEFAULT 'Offline',
                    status_until TIMESTAMP NULL,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS call_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_employee VARCHAR(50) NOT NULL,
                    ticket_id VARCHAR(50) NOT NULL,
                    ticket_subject TEXT NOT NULL,
                    caller_name TEXT NOT NULL,
                    call_info JSON NOT NULL,
                    status TEXT DEFAULT 'pending', -- e.g., pending, answered, declined, completed
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (target_employee) REFERENCES employees_data_table(username)
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_username ON employees_data_table(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_role ON employees_data_table(role_in_company)") # Kept for now, might be useful
            conn.execute("CREATE INDEX IF NOT EXISTS idx_active ON employees_data_table(is_active)")

            self._migrate_database(conn) # Pass connection

            conn.commit()
            # print("✅ Employee database initialized in optimized_project")

    def _migrate_database(self, conn: sqlite3.Connection):
        """Migrate existing database to add availability columns if needed."""
        # Check if availability columns exist
        cursor = conn.execute("PRAGMA table_info(employees_data_table)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'availability_status' not in columns:
            conn.execute("ALTER TABLE employees_data_table ADD COLUMN availability_status TEXT DEFAULT 'Offline'")
        if 'status_until' not in columns:
            conn.execute("ALTER TABLE employees_data_table ADD COLUMN status_until TIMESTAMP NULL")
        if 'last_seen' not in columns:
            conn.execute("ALTER TABLE employees_data_table ADD COLUMN last_seen TIMESTAMP")
            conn.execute("UPDATE employees_data_table SET last_seen = CURRENT_TIMESTAMP WHERE last_seen IS NULL")

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='call_notifications'")
        if not cursor.fetchone():
            conn.execute("""
                CREATE TABLE call_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_employee VARCHAR(50) NOT NULL,
                    ticket_id VARCHAR(50) NOT NULL,
                    ticket_subject TEXT NOT NULL,
                    caller_name TEXT NOT NULL,
                    call_info JSON NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (target_employee) REFERENCES employees_data_table(username)
                )
            """)

    def create_employee(self, username: str, full_name: str, role_in_company: str,
                       job_description: str, expertise: str, responsibilities: str) -> Tuple[bool, str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT username FROM employees_data_table WHERE username = ?", (username,))
                if cursor.fetchone():
                    return False, f"Username '{username}' already exists"
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
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM employees_data_table WHERE username = ? AND is_active = TRUE", (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Database error in get_employee_by_username: {e}")
            return None

    def get_all_employees(self, active_only: bool = True) -> List[Dict]:
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
            print(f"Database error in get_all_employees: {e}")
            return []

    # Methods to be pruned (commented out for now, will remove if confirmed):
    # def get_employees_by_role(self, role: str) -> List[Dict]: ...
    # def get_employees_by_expertise(self, expertise: str) -> List[Dict]: ...
    # def update_employee(self, username: str, **kwargs) -> Tuple[bool, str]: ... # Only specific updates are exposed now
    # def deactivate_employee(self, username: str) -> Tuple[bool, str]: ... # Use update_employee with is_active=False if needed by admin UI

    def update_employee_record(self, username: str, data_to_update: Dict[str, Any]) -> Tuple[bool, str]:
        """General purpose employee update, used carefully by admin UI if needed."""
        valid_fields = {'full_name', 'role_in_company', 'job_description', 'expertise', 'responsibilities', 'is_active'}
        update_fields = {k: v for k, v in data_to_update.items() if k in valid_fields}
        if not update_fields:
            return False, "No valid fields provided for update."

        update_fields['updated_at'] = datetime.now().isoformat()
        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [username]

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"UPDATE employees_data_table SET {set_clause} WHERE username = ?", values)
                if cursor.rowcount == 0:
                    return False, f"Employee '{username}' not found or no changes made."
                conn.commit()
                return True, f"Employee '{username}' updated successfully."
        except sqlite3.Error as e:
            return False, f"Database error updating employee: {str(e)}"


    def update_employee_status(self, username: str, status: str, until_time: Optional[str] = None) -> Tuple[bool, str]:
        valid_statuses = ['Available', 'In Meeting', 'Busy', 'Do Not Disturb', 'Offline']
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE employees_data_table
                    SET availability_status = ?, status_until = ?, last_seen = CURRENT_TIMESTAMP
                    WHERE username = ?
                """, (status, until_time, username))
                if conn.total_changes == 0: # Changed from cursor.rowcount as execute doesn't return cursor for UPDATE
                    return False, f"Employee '{username}' not found"
                conn.commit()
                return True, f"Status for '{username}' updated to '{status}'"
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

    def update_last_seen(self, username: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE employees_data_table SET last_seen = CURRENT_TIMESTAMP WHERE username = ?", (username,))
                conn.commit()
                return conn.total_changes > 0
        except sqlite3.Error:
            return False

    def get_employee_availability(self, username: str) -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT username, full_name, availability_status, status_until, last_seen
                    FROM employees_data_table WHERE username = ? AND is_active = TRUE
                """, (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error:
            return None

    def auto_cleanup_expired_statuses(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE employees_data_table SET availability_status = 'Available', status_until = NULL
                    WHERE status_until IS NOT NULL AND status_until < CURRENT_TIMESTAMP
                """)
                conn.execute("""
                    UPDATE employees_data_table SET availability_status = 'Offline'
                    WHERE datetime(last_seen) < datetime('now', '-15 minutes') AND availability_status != 'Offline'
                """)
                conn.commit()
        except sqlite3.Error:
            pass # Silently fail on cleanup

    def get_employee_stats(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM employees_data_table WHERE is_active = TRUE")
                total_active = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM employees_data_table")
                total_all = cursor.fetchone()[0]
                cursor = conn.execute("""
                    SELECT role_in_company, COUNT(*) as count FROM employees_data_table
                    WHERE is_active = TRUE GROUP BY role_in_company ORDER BY count DESC
                """)
                role_distribution = dict(cursor.fetchall())
                return {
                    "total_active": total_active, "total_all": total_all,
                    "role_distribution": role_distribution, "database_path": str(self.db_path)
                }
        except sqlite3.Error as e:
            return {"error": f"Database error: {str(e)}"}

    def backup_database(self) -> Tuple[bool, str]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_path = self.backup_dir / f"employees_backup_{timestamp}.db"
            shutil.copy2(self.db_path, backup_file_path)
            return True, f"Database backed up to {backup_file_path}"
        except Exception as e:
            return False, f"Backup failed: {str(e)}"

    def search_employees(self, search_term: str) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                term = f"%{search_term}%"
                cursor = conn.execute("""
                    SELECT * FROM employees_data_table WHERE is_active = TRUE AND
                    (full_name LIKE ? OR role_in_company LIKE ? OR expertise LIKE ? OR responsibilities LIKE ?)
                    ORDER BY full_name
                """, (term, term, term, term))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error in search_employees: {e}")
            return []

    def create_call_notification(self, target_employee: str, ticket_id: str, ticket_subject: str,
                                caller_name: str, call_info: Dict) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO call_notifications (target_employee, ticket_id, ticket_subject, caller_name, call_info)
                    VALUES (?, ?, ?, ?, ?)
                """, (target_employee, ticket_id, ticket_subject, caller_name, json.dumps(call_info)))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error creating call notification: {e}")
            return False

    def get_pending_calls(self, employee_username: str) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM call_notifications WHERE target_employee = ? AND status = 'pending'
                    ORDER BY created_at DESC
                """, (employee_username,))
                calls = []
                for row in cursor.fetchall():
                    call = dict(row)
                    try:
                        call['call_info'] = json.loads(call['call_info'])
                    except json.JSONDecodeError:
                        call['call_info'] = {} # Default if JSON is malformed
                    calls.append(call)
                return calls
        except sqlite3.Error as e:
            print(f"Error getting pending calls: {e}")
            return []

    def update_call_status(self, call_id: int, status: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE call_notifications SET status = ? WHERE id = ?", (status, call_id))
                conn.commit()
                return conn.total_changes > 0
        except sqlite3.Error as e:
            print(f"Error updating call status: {e}")
            return False

    # def clear_old_calls(self, hours: int = 24) -> bool: ... # Pruned as not used by core UI

# No singleton instance here. It will be instantiated by the application where needed,
# passing the correct project_root_path.
# Example:
# from pathlib import Path
# current_project_root = Path(__file__).resolve().parent.parent # Assuming this file is in optimized_project/data_management
# db_manager_instance = DatabaseManager(project_root_path=current_project_root)

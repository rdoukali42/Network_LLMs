#!/usr/bin/env python3
"""
Cleanup Script - Remove all tickets, call history, and notifications
This script will completely clean all ticket data, call notifications, and logs.
"""

import sqlite3
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List

# Get project root directory
PROJECT_ROOT = Path(__file__).parent


class DataCleanup:
    """Handles cleanup of all system data."""
    
    def __init__(self):
        """Initialize cleanup manager."""
        self.db_path = PROJECT_ROOT / "data" / "databases" / "employees.db"
        self.tickets_json = PROJECT_ROOT / "front" / "tickets.json"
        self.logs_dir = PROJECT_ROOT / "logs"
        self.front_logs_dir = PROJECT_ROOT / "front" / "logs"
        self.chroma_db_dir = PROJECT_ROOT / "data" / "chroma_db"
        self.front_chroma_db_dir = PROJECT_ROOT / "front" / "data" / "chroma_db"
        
        # Track what will be cleaned
        self.cleanup_summary = []
    
    def clear_database_notifications(self) -> bool:
        """Clear all call notifications from the database."""
        try:
            if not self.db_path.exists():
                self.cleanup_summary.append("❌ Database not found - skipping database cleanup")
                return True
            
            with sqlite3.connect(self.db_path) as conn:
                # Count existing notifications
                cursor = conn.execute("SELECT COUNT(*) FROM call_notifications")
                notification_count = cursor.fetchone()[0]
                
                if notification_count > 0:
                    # Clear all call notifications
                    conn.execute("DELETE FROM call_notifications")
                    conn.commit()
                    self.cleanup_summary.append(f"✅ Removed {notification_count} call notifications from database")
                else:
                    self.cleanup_summary.append("ℹ️ No call notifications found in database")
                
                return True
                
        except Exception as e:
            self.cleanup_summary.append(f"❌ Failed to clear database notifications: {str(e)}")
            return False
    
    def clear_tickets_json(self) -> bool:
        """Clear all tickets from tickets.json file."""
        try:
            if not self.tickets_json.exists():
                self.cleanup_summary.append("ℹ️ tickets.json not found - skipping")
                return True
            
            # Read current tickets to count them
            with open(self.tickets_json, 'r') as f:
                tickets = json.load(f)
            
            ticket_count = len(tickets) if isinstance(tickets, list) else 0
            
            if ticket_count > 0:
                # Clear tickets by writing empty array
                with open(self.tickets_json, 'w') as f:
                    json.dump([], f, indent=2)
                
                self.cleanup_summary.append(f"✅ Removed {ticket_count} tickets from tickets.json")
            else:
                self.cleanup_summary.append("ℹ️ No tickets found in tickets.json")
            
            return True
            
        except Exception as e:
            self.cleanup_summary.append(f"❌ Failed to clear tickets.json: {str(e)}")
            return False
    
    def clear_log_files(self) -> bool:
        """Clear all log files."""
        success = True
        log_dirs = [self.logs_dir, self.front_logs_dir]
        
        for log_dir in log_dirs:
            try:
                if not log_dir.exists():
                    continue
                
                log_files = list(log_dir.glob("*.log"))
                if log_files:
                    for log_file in log_files:
                        # Clear log file content but keep the file
                        with open(log_file, 'w') as f:
                            f.write(f"# Log cleared on {datetime.now().isoformat()}\n")
                    
                    self.cleanup_summary.append(f"✅ Cleared {len(log_files)} log files in {log_dir.name}/")
                else:
                    self.cleanup_summary.append(f"ℹ️ No log files found in {log_dir.name}/")
                    
            except Exception as e:
                self.cleanup_summary.append(f"❌ Failed to clear logs in {log_dir.name}/: {str(e)}")
                success = False
        
        return success
    
    def clear_vector_databases(self) -> bool:
        """Clear vector database files (ChromaDB)."""
        success = True
        chroma_dirs = [self.chroma_db_dir, self.front_chroma_db_dir]
        
        for chroma_dir in chroma_dirs:
            try:
                if not chroma_dir.exists():
                    continue
                
                # Count files before deletion
                db_files = list(chroma_dir.rglob("*"))
                db_files = [f for f in db_files if f.is_file()]
                
                if db_files:
                    # Remove the entire chroma_db directory and recreate it
                    shutil.rmtree(chroma_dir)
                    chroma_dir.mkdir(parents=True, exist_ok=True)
                    
                    self.cleanup_summary.append(f"✅ Cleared vector database in {chroma_dir.relative_to(PROJECT_ROOT)} ({len(db_files)} files)")
                else:
                    self.cleanup_summary.append(f"ℹ️ No vector database files found in {chroma_dir.relative_to(PROJECT_ROOT)}")
                    
            except Exception as e:
                self.cleanup_summary.append(f"❌ Failed to clear vector database in {chroma_dir.relative_to(PROJECT_ROOT)}: {str(e)}")
                success = False
        
        return success
    
    def backup_before_cleanup(self) -> bool:
        """Create a backup before cleanup (optional safety measure)."""
        try:
            backup_dir = PROJECT_ROOT / "data" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"cleanup_backup_{timestamp}"
            
            # Backup tickets.json if it exists
            if self.tickets_json.exists():
                backup_tickets = backup_dir / f"{backup_name}_tickets.json"
                shutil.copy2(self.tickets_json, backup_tickets)
                self.cleanup_summary.append(f"✅ Backed up tickets to {backup_tickets.name}")
            
            # Backup database if it exists
            if self.db_path.exists():
                backup_db = backup_dir / f"{backup_name}_employees.db"
                shutil.copy2(self.db_path, backup_db)
                self.cleanup_summary.append(f"✅ Backed up database to {backup_db.name}")
            
            return True
            
        except Exception as e:
            self.cleanup_summary.append(f"⚠️ Backup failed (continuing anyway): {str(e)}")
            return False
    
    def run_full_cleanup(self, create_backup: bool = True) -> bool:
        """Run complete data cleanup."""
        print("🧹 Starting complete data cleanup...")
        print("=" * 60)
        
        success = True
        
        # Optional backup
        if create_backup:
            self.backup_before_cleanup()
        
        # Run all cleanup operations
        success &= self.clear_database_notifications()
        success &= self.clear_tickets_json()
        success &= self.clear_log_files()
        success &= self.clear_vector_databases()
        
        # Print summary
        print("\n📋 Cleanup Summary:")
        print("-" * 40)
        for item in self.cleanup_summary:
            print(f"  {item}")
        
        print("\n" + "=" * 60)
        if success:
            print("✅ Cleanup completed successfully!")
            print("\n🔄 Note: You may need to restart the application for changes to take effect.")
        else:
            print("⚠️ Cleanup completed with some errors. Check the summary above.")
        
        return success


def main():
    """Main cleanup execution."""
    print("🚨 WARNING: This will permanently delete all tickets, call notifications, and logs!")
    print("This action cannot be undone.")
    print()
    
    # Ask for confirmation
    try:
        confirm = input("Are you sure you want to continue? Type 'yes' to confirm: ").strip().lower()
        if confirm != 'yes':
            print("❌ Cleanup cancelled.")
            return
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled.")
        return
    
    # Ask about backup
    try:
        backup_choice = input("Create backup before cleanup? (y/n) [default: y]: ").strip().lower()
        create_backup = backup_choice != 'n'
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled.")
        return
    
    # Run cleanup
    cleanup = DataCleanup()
    cleanup.run_full_cleanup(create_backup=create_backup)


if __name__ == "__main__":
    main()

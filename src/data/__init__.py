"""
Data module for data access and persistence.
Contains repositories, models, and database management.
"""

from .database_manager import DatabaseManager, db_manager
from .repositories import TicketRepository, UserRepository, BaseRepository

__all__ = [
    'DatabaseManager',
    'db_manager',
    'TicketRepository',
    'UserRepository', 
    'BaseRepository',
]

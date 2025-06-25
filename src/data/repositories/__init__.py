"""
Repositories package for data access layer.
Implements the Repository pattern for clean data access.
"""

from core.base_repository import BaseRepository
from .ticket_repository import TicketRepository
from .user_repository import UserRepository

__all__ = [
    'BaseRepository',
    'TicketRepository',
    'UserRepository'
]

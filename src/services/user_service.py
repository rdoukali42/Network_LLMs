"""
User service for managing user-related business logic.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from data.models.user import User, AvailabilityStatus
from data.repositories.user_repository import UserRepository
from core.base_service import BaseService
from utils.exceptions import ValidationError, BusinessLogicError, AuthenticationError
from config.settings import settings
import hashlib
import secrets


class UserService(BaseService):
    """
    Service class handling user-related business logic.
    """
    
    def __init__(self, user_repository=None, settings=None):
        super().__init__(settings or "UserService")
        self.user_repository = user_repository or UserRepository()
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_user(
        self,
        username: str,
        full_name: str,
        role_in_company: str,
        job_description: str,
        expertise: str,
        availability_status: AvailabilityStatus = AvailabilityStatus.OFFLINE,
        password: Optional[str] = None
    ) -> User:
        """
        Create a new user.
        
        Args:
            username: Unique username
            full_name: User's full name  
            role_in_company: Role in the company
            job_description: Job description
            expertise: Areas of expertise
            availability_status: Initial availability status
            password: Optional password for authentication
            
        Returns:
            Created user
            
        Raises:
            ValidationError: If validation fails
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate inputs
            self._validate_user_creation(username, full_name, role_in_company, job_description)
            
            # Check if username already exists
            existing_user = self.user_repository.get_by_username(username)
            if existing_user:
                raise BusinessLogicError(f"Username '{username}' already exists")
            
            # Create user object
            user = User(
                username=username.strip(),
                full_name=full_name.strip(),
                role_in_company=role_in_company.strip(),
                job_description=job_description.strip(),
                expertise=expertise.strip() if expertise else "",
                availability_status=availability_status,
                last_seen=datetime.now(),
                is_active=True
            )
            
            # Set password if provided
            if password:
                user.password_hash = self._hash_password(password)
            
            # Save to repository
            created_user = self.user_repository.create(user)
            
            self.logger.info(f"User created: {created_user.username} (ID: {created_user.id})")
            
            return created_user
            
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authenticated user or None
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            if not username or not password:
                raise AuthenticationError("Username and password are required")
            
            user = self.user_repository.get_by_username(username)
            if not user:
                self.logger.warning(f"Authentication failed: User '{username}' not found")
                raise AuthenticationError("Invalid username or password")
            
            if not user.is_active:
                self.logger.warning(f"Authentication failed: User '{username}' is inactive")
                raise AuthenticationError("Account is inactive")
            
            # Check password if user has one
            if user.password_hash:
                hashed_password = self._hash_password(password)
                if user.password_hash != hashed_password:
                    self.logger.warning(f"Authentication failed: Invalid password for '{username}'")
                    raise AuthenticationError("Invalid username or password")
            
            # Update last seen
            user.last_seen = datetime.now()
            self.user_repository.update(user)
            
            self.logger.info(f"User authenticated successfully: {username}")
            return user
            
        except AuthenticationError:
            raise
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise AuthenticationError("Authentication failed due to system error")
    
    def create_session(self, user: User, session_duration_hours: int = 24) -> str:
        """
        Create a new user session.
        
        Args:
            user: Authenticated user
            session_duration_hours: Session duration in hours
            
        Returns:
            Session token
        """
        try:
            session_token = secrets.token_urlsafe(32)
            session_data = {
                "user_id": user.id,
                "username": user.username,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=session_duration_hours),
                "last_activity": datetime.now()
            }
            
            self._active_sessions[session_token] = session_data
            
            self.logger.info(f"Session created for user {user.username}: {session_token[:8]}...")
            return session_token
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise BusinessLogicError("Failed to create user session")
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """
        Validate a session token and return the user.
        
        Args:
            session_token: Session token
            
        Returns:
            User if session is valid, None otherwise
        """
        try:
            if not session_token or session_token not in self._active_sessions:
                return None
            
            session_data = self._active_sessions[session_token]
            
            # Check if session has expired
            if datetime.now() > session_data["expires_at"]:
                del self._active_sessions[session_token]
                self.logger.info(f"Session expired: {session_token[:8]}...")
                return None
            
            # Update last activity
            session_data["last_activity"] = datetime.now()
            
            # Get user
            user = self.user_repository.get_by_id(session_data["user_id"])
            if not user or not user.is_active:
                del self._active_sessions[session_token]
                return None
            
            return user
            
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a session token.
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if session was invalidated
        """
        try:
            if session_token in self._active_sessions:
                del self._active_sessions[session_token]
                self.logger.info(f"Session invalidated: {session_token[:8]}...")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Session invalidation error: {e}")
            return False
    
    def update_availability(self, user_id: int, status: AvailabilityStatus) -> User:
        """
        Update user availability status.
        
        Args:
            user_id: User ID
            status: New availability status
            
        Returns:
            Updated user
        """
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                raise BusinessLogicError(f"User {user_id} not found")
            
            user.availability_status = status
            user.last_seen = datetime.now()
            
            updated_user = self.user_repository.update(user)
            
            self.logger.info(f"User {user.username} availability updated to {status.value}")
            return updated_user
            
        except Exception as e:
            self.logger.error(f"Failed to update user availability: {e}")
            raise
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password was changed successfully
        """
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                raise BusinessLogicError(f"User {user_id} not found")
            
            # Validate current password if user has one
            if user.password_hash:
                current_hash = self._hash_password(current_password)
                if user.password_hash != current_hash:
                    raise AuthenticationError("Current password is incorrect")
            
            # Validate new password
            self._validate_password(new_password)
            
            # Set new password
            user.password_hash = self._hash_password(new_password)
            self.user_repository.update(user)
            
            self.logger.info(f"Password changed for user {user.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to change password: {e}")
            raise
    
    def get_user_profile(self, user_id: int) -> Optional[User]:
        """Get user profile by ID."""
        try:
            return self.user_repository.get_by_id(user_id)
        except Exception as e:
            self.logger.error(f"Failed to get user profile: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user profile by username."""
        self.logger.debug(f"[DEBUG] UserService.get_user_by_username called for '{username}'")
        self.logger.debug(f"[DEBUG] UserService using repository: {type(self.user_repository).__name__} with db_path: {getattr(self.user_repository, 'db_path', 'N/A')}")
        try:
            user = self.user_repository.get_by_username(username)
            if user:
                self.logger.debug(f"[DEBUG] UserService.get_user_by_username: Found user '{username}' -> {user.full_name}")
            else:
                self.logger.debug(f"[DEBUG] UserService.get_user_by_username: User '{username}' not found")
            return user
        except Exception as e:
            self.logger.error(f"[DEBUG] UserService.get_user_by_username failed for '{username}': {e}")
            raise
    
    def search_users(self, query: str, limit: int = 50) -> List[User]:
        """Search users by various fields."""
        try:
            return self.user_repository.search(query, limit)
        except Exception as e:
            self.logger.error(f"Failed to search users: {e}")
            raise
    
    def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role."""
        try:
            return self.user_repository.get_by_role(role)
        except Exception as e:
            self.logger.error(f"Failed to get users by role: {e}")
            raise
    
    def get_online_users(self, minutes_threshold: int = 30) -> List[User]:
        """Get users who were online within the specified threshold."""
        try:
            return self.user_repository.get_recently_active_users(minutes_threshold)
        except Exception as e:
            self.logger.error(f"Failed to get online users: {e}")
            raise
    
    def deactivate_user(self, user_id: int, deactivated_by: int) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID to deactivate
            deactivated_by: User ID performing the deactivation
            
        Returns:
            True if user was deactivated
        """
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                raise BusinessLogicError(f"User {user_id} not found")
            
            # Check permissions
            deactivator = self.user_repository.get_by_id(deactivated_by)
            if not deactivator:
                raise BusinessLogicError("Invalid deactivator user")
            
            # Prevent self-deactivation (except for admin)
            if user_id == deactivated_by and not self._is_admin(deactivator):
                raise BusinessLogicError("Cannot deactivate your own account")
            
            user.is_active = False
            user.availability_status = AvailabilityStatus.OFFLINE
            self.user_repository.update(user)
            
            # Invalidate all sessions for this user
            self._invalidate_user_sessions(user_id)
            
            self.logger.info(f"User {user.username} deactivated by {deactivator.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate user: {e}")
            raise
    
    def _validate_user_creation(self, username: str, full_name: str, role_in_company: str, job_description: str):
        """Validate user creation parameters."""
        if not username or len(username.strip()) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if len(username) > 50:
            raise ValidationError("Username cannot exceed 50 characters")
        
        if not full_name or len(full_name.strip()) < 2:
            raise ValidationError("Full name must be at least 2 characters long")
        
        if len(full_name) > 100:
            raise ValidationError("Full name cannot exceed 100 characters")
        
        if not role_in_company or len(role_in_company.strip()) < 2:
            raise ValidationError("Role in company is required")
        
        if not job_description or len(job_description.strip()) < 10:
            raise ValidationError("Job description must be at least 10 characters long")
    
    def _validate_password(self, password: str):
        """Validate password strength."""
        if not password or len(password) < settings.security.password_min_length:
            raise ValidationError(f"Password must be at least {settings.security.password_min_length} characters long")
        
        if settings.security.require_password_complexity:
            if not any(c.isupper() for c in password):
                raise ValidationError("Password must contain at least one uppercase letter")
            
            if not any(c.islower() for c in password):
                raise ValidationError("Password must contain at least one lowercase letter")
            
            if not any(c.isdigit() for c in password):
                raise ValidationError("Password must contain at least one digit")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _is_admin(self, user: User) -> bool:
        """Check if user has admin privileges."""
        admin_roles = ["admin", "administrator", "super_admin"]
        return user.role_in_company.lower() in admin_roles
    
    def _invalidate_user_sessions(self, user_id: int):
        """Invalidate all sessions for a specific user."""
        sessions_to_remove = []
        for token, session_data in self._active_sessions.items():
            if session_data["user_id"] == user_id:
                sessions_to_remove.append(token)
        
        for token in sessions_to_remove:
            del self._active_sessions[token]
        
        self.logger.info(f"Invalidated {len(sessions_to_remove)} sessions for user {user_id}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get user service statistics."""
        try:
            user_stats = self.user_repository.get_user_stats()
            active_sessions = len(self._active_sessions)
            
            return {
                **user_stats,
                "active_sessions": active_sessions,
                "service_status": "healthy",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get service stats: {e}")
            return {
                "service_status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    def get_service_name(self) -> str:
        """Return the service name."""
        return "UserService"

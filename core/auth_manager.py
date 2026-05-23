import secrets
from datetime import datetime, timedelta
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

import config
from models import get_session, User, Session as SessionModel
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthError(Exception):
    pass


class AuthManager:
    """
    Token-based auth using DB sessions table.
    Token = URL-safe random 48 chars. Stored hashed? No -- stored raw (single-process LAN demo).
    Session expires after config.SESSION_EXPIRE_HOURS.
    """

    TOKEN_BYTES = 36  # ~48 chars URL-safe

    # ---------- User CRUD ----------

    def register(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: str = "user",
    ) -> dict:
        username = (username or "").strip()
        if not username or len(username) < 3:
            raise AuthError("Username must be at least 3 characters")
        if not password or len(password) < 6:
            raise AuthError("Password must be at least 6 characters")
        if role not in ("admin", "user"):
            raise AuthError(f"Invalid role: {role}")

        with get_session() as s:
            existing = s.query(User).filter(User.username == username).one_or_none()
            if existing:
                raise AuthError(f"Username already exists: {username}")

            if email:
                existing_email = s.query(User).filter(User.email == email).one_or_none()
                if existing_email:
                    raise AuthError(f"Email already registered: {email}")

            user = User(
                username=username,
                password=generate_password_hash(password),
                email=email,
                role=role,
                is_active=True,
            )
            s.add(user)
            s.commit()
            s.refresh(user)
            logger.info(f"User registered: id={user.id} username={username} role={role}")
            return user.to_dict()

    def login(self, username: str, password: str) -> dict:
        """Verify credentials, create session, return user + token."""
        username = (username or "").strip()
        if not username or not password:
            raise AuthError("Username and password required")

        with get_session() as s:
            user = s.query(User).filter(User.username == username).one_or_none()
            if user is None:
                raise AuthError("Invalid credentials")
            if not user.is_active:
                raise AuthError("Account is disabled")
            if not check_password_hash(user.password, password):
                raise AuthError("Invalid credentials")

            token = secrets.token_urlsafe(self.TOKEN_BYTES)
            expires_at = datetime.utcnow() + timedelta(hours=config.SESSION_EXPIRE_HOURS)
            session = SessionModel(
                user_id=user.id,
                token=token,
                expires_at=expires_at,
            )
            s.add(session)
            s.commit()

            logger.info(f"Login OK: user_id={user.id} username={username}")
            return {
                "user": user.to_dict(),
                "token": token,
                "expires_at": expires_at.isoformat(),
            }

    def logout(self, token: str) -> bool:
        if not token:
            return False
        with get_session() as s:
            session = s.query(SessionModel).filter(SessionModel.token == token).one_or_none()
            if session is None:
                return False
            s.delete(session)
            s.commit()
            logger.info(f"Logout OK: user_id={session.user_id}")
            return True

    # ---------- Verification ----------

    def verify_token(self, token: str) -> Optional[dict]:
        """Return user dict if token valid + not expired, else None."""
        if not token:
            return None
        with get_session() as s:
            session = s.query(SessionModel).filter(SessionModel.token == token).one_or_none()
            if session is None:
                return None
            if session.is_expired():
                s.delete(session)
                s.commit()
                return None
            user = s.query(User).filter(User.id == session.user_id).one_or_none()
            if user is None or not user.is_active:
                return None
            return user.to_dict()

    def cleanup_expired(self) -> int:
        """Delete expired sessions. Returns count deleted."""
        with get_session() as s:
            now = datetime.utcnow()
            expired = s.query(SessionModel).filter(SessionModel.expires_at < now).all()
            count = len(expired)
            for e in expired:
                s.delete(e)
            s.commit()
            if count:
                logger.info(f"Cleaned {count} expired sessions")
            return count

    # ---------- Bootstrap ----------

    def ensure_admin(self) -> Optional[dict]:
        """Create default admin if no admin exists. Idempotent."""
        with get_session() as s:
            existing_admin = s.query(User).filter(User.role == "admin").first()
            if existing_admin:
                return None
            existing = s.query(User).filter(User.username == config.ADMIN_USERNAME).one_or_none()
            if existing:
                # Promote to admin
                existing.role = "admin"
                existing.is_active = True
                s.commit()
                logger.info(f"Promoted existing user to admin: {config.ADMIN_USERNAME}")
                return existing.to_dict()

            admin = User(
                username=config.ADMIN_USERNAME,
                password=generate_password_hash(config.ADMIN_PASSWORD),
                email=config.ADMIN_EMAIL,
                role="admin",
                is_active=True,
            )
            s.add(admin)
            s.commit()
            s.refresh(admin)
            logger.warning(
                f"Bootstrap admin created: username={config.ADMIN_USERNAME} "
                f"(CHANGE PASSWORD via .env in production)"
            )
            return admin.to_dict()


_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    global _manager
    if _manager is None:
        _manager = AuthManager()
    return _manager 
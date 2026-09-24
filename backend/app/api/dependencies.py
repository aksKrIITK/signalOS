import uuid
from typing import AsyncGenerator, Callable, List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.db.repositories.organization_repo import UserRepository
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not auth or not auth.credentials:
        # For development / initial access, create or return demo user
        user_repo = UserRepository(db)
        demo_user = await user_repo.get_by_email("demo@signalos.ai")
        if demo_user:
            return demo_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(auth.credentials)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedError("Invalid token payload")
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User inactive or not found")
    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    async def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(f"User role '{current_user.role}' is not authorized for this resource")
        return current_user

    return _role_checker

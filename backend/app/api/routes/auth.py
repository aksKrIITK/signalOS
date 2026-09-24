import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.organization_repo import OrganizationRepository, UserRepository
from app.core.security import create_access_token, get_password_hash, verify_password, UserRole
from app.schemas.auth import LoginRequest, Token, UserRegisterRequest, UserResponse
from app.api.dependencies import get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org = await org_repo.create(name=data.organization_name)
    hashed_pwd = get_password_hash(data.password)

    user = await user_repo.create(
        organization_id=org.id,
        email=data.email,
        hashed_password=hashed_pwd,
        full_name=data.full_name,
        role=data.role or UserRole.OWNER,
        is_active=True,
    )
    await db.commit()

    token = create_access_token(subject=user.id, organization_id=org.id, role=user.role)
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        organization_id=org.id,
        role=user.role,
        email=user.email,
    )


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.id, organization_id=user.organization_id, role=user.role)
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role,
        email=user.email,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

import uuid
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(
        self,
        id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
    ) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        if organization_id is not None and hasattr(self.model, "organization_id"):
            query = query.where(self.model.organization_id == organization_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list(
        self,
        organization_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 50,
        order_by: Any = None,
    ) -> Sequence[ModelType]:
        query = select(self.model)
        if organization_id is not None and hasattr(self.model, "organization_id"):
            query = query.where(self.model.organization_id == organization_id)
        if order_by is not None:
            query = query.order_by(order_by)
        elif hasattr(self.model, "created_at"):
            query = query.order_by(self.model.created_at.desc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(self, organization_id: Optional[uuid.UUID] = None) -> int:
        query = select(func.count()).select_from(self.model)
        if organization_id is not None and hasattr(self.model, "organization_id"):
            query = query.where(self.model.organization_id == organization_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs: Any) -> ModelType:
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> bool:
        await self.db.delete(instance)
        await self.db.flush()
        return True

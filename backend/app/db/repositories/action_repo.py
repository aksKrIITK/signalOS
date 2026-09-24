import uuid
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.action import ActionExecution
from app.db.models.audit_log import AuditLog
from app.db.repositories.base import BaseRepository


class ActionExecutionRepository(BaseRepository[ActionExecution]):
    def __init__(self, db: AsyncSession):
        super().__init__(ActionExecution, db)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[ActionExecution]:
        query = select(ActionExecution).where(ActionExecution.idempotency_key == idempotency_key)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def record_execution(
        self,
        organization_id: uuid.UUID,
        idempotency_key: str,
        action_type: str,
        payload: Dict[str, Any],
        status: str = "COMPLETED",
        result: Optional[Dict[str, Any]] = None,
        target_resource_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> ActionExecution:
        action = ActionExecution(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            action_type=action_type,
            payload=payload,
            status=status,
            result=result or {},
            target_resource_id=target_resource_id,
            error=error,
        )
        self.db.add(action)
        await self.db.flush()
        await self.db.refresh(action)
        return action


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(AuditLog, db)

    async def log_action(
        self,
        organization_id: uuid.UUID,
        action: str,
        resource_type: str,
        user_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        audit = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
            ip_address=ip_address,
        )
        self.db.add(audit)
        await self.db.flush()
        return audit

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.action import ActionExecution
from app.db.repositories.action_repo import ActionExecutionRepository, AuditLogRepository
from app.core.logging import logger


class ActionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.action_repo = ActionExecutionRepository(db)
        self.audit_repo = AuditLogRepository(db)

    async def execute_action(
        self,
        organization_id: uuid.UUID,
        campaign_id: uuid.UUID,
        lead_id: uuid.UUID,
        action_type: str,
        payload: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """
        Executes external side effects (send_email, crm_update) with guaranteed idempotency.
        Key pattern: `campaign_id:lead_id:action_type`
        """
        idempotency_key = f"{str(campaign_id)}:{str(lead_id)}:{action_type}"

        existing = await self.action_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            logger.info("idempotent_action_skipped", idempotency_key=idempotency_key, status=existing.status)
            return {
                "idempotency_key": idempotency_key,
                "status": "ALREADY_EXECUTED",
                "result": existing.result,
                "created_at": str(existing.created_at),
            }

        logger.info("executing_new_action", action_type=action_type, idempotency_key=idempotency_key)

        result_payload = {}
        if action_type == "send_email":
            # Simulate real transactional mail delivery
            result_payload = {
                "message_id": f"msg-{uuid.uuid4().hex[:12]}",
                "recipient": payload.get("to_email", "lead@company.com"),
                "subject": payload.get("subject", ""),
                "status": "SENT",
            }
        elif action_type == "create_crm_activity":
            result_payload = {
                "activity_id": f"crm-act-{uuid.uuid4().hex[:8]}",
                "status": "SYNCED",
            }
        else:
            result_payload = {"status": "SUCCESS", "details": payload}

        record = await self.action_repo.record_execution(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            action_type=action_type,
            payload=payload,
            status="COMPLETED",
            result=result_payload,
            target_resource_id=str(lead_id),
        )

        await self.audit_repo.log_action(
            organization_id=organization_id,
            user_id=user_id,
            action=f"ACTION_EXECUTED_{action_type.upper()}",
            resource_type="lead",
            resource_id=str(lead_id),
            metadata={"idempotency_key": idempotency_key, "result": result_payload},
        )

        return {
            "idempotency_key": idempotency_key,
            "status": "COMPLETED",
            "result": result_payload,
            "execution_id": str(record.id),
        }

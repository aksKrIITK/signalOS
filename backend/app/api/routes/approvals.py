import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.agent_run import AgentRunStatus
from app.api.dependencies import get_current_user
from app.db.repositories.agent_run_repo import AgentRunRepository
from app.schemas.agent import AgentRunResponse, ApprovalActionRequest
from app.services.action_service import ActionService

router = APIRouter(prefix="/approvals", tags=["Human Approvals"])


@router.get("", response_model=List[AgentRunResponse])
async def list_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = AgentRunRepository(db)
    return await repo.list_runs(
        organization_id=current_user.organization_id,
        status=AgentRunStatus.WAITING_APPROVAL,
    )


@router.post("/{id}/approve")
async def approve_agent_action(
    id: uuid.UUID,
    data: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run_repo = AgentRunRepository(db)
    run = await run_repo.get_by_id(id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    action_service = ActionService(db)
    output = dict(run.output_json)

    # Execute approved action with idempotency
    result = await action_service.execute_action(
        organization_id=current_user.organization_id,
        campaign_id=run.campaign_id or uuid.uuid4(),
        lead_id=run.lead_id or uuid.uuid4(),
        action_type="send_email",
        payload={
            "subject": data.edited_subject or output.get("email_subject", "Outreach"),
            "body": data.edited_body or output.get("email_body", ""),
        },
        user_id=current_user.id,
    )

    output["action_executed"] = True
    output["action_result"] = result
    await run_repo.update(run, status=AgentRunStatus.COMPLETED, output_json=output)
    await db.commit()

    return {
        "status": "APPROVED_AND_EXECUTED",
        "run_id": str(id),
        "execution": result,
    }


@router.post("/{id}/reject")
async def reject_agent_action(
    id: uuid.UUID,
    data: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run_repo = AgentRunRepository(db)
    run = await run_repo.get_by_id(id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    output = dict(run.output_json)
    output["rejection_feedback"] = data.feedback or "Rejected by reviewer"
    await run_repo.update(run, status="REJECTED", output_json=output)
    await db.commit()

    return {
        "status": "REJECTED",
        "run_id": str(id),
        "feedback": data.feedback,
    }

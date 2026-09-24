import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.agent_run import AgentRun, ToolCall
from app.db.repositories.base import BaseRepository


class AgentRunRepository(BaseRepository[AgentRun]):
    def __init__(self, db: AsyncSession):
        super().__init__(AgentRun, db)

    async def get_with_tools(self, id: uuid.UUID, organization_id: Optional[uuid.UUID] = None) -> Optional[AgentRun]:
        query = select(AgentRun).where(AgentRun.id == id).options(
            selectinload(AgentRun.tool_calls)
        )
        if organization_id:
            query = query.where(AgentRun.organization_id == organization_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_runs(
        self,
        organization_id: uuid.UUID,
        campaign_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[AgentRun]:
        query = select(AgentRun).where(AgentRun.organization_id == organization_id)
        if campaign_id:
            query = query.where(AgentRun.campaign_id == campaign_id)
        if status:
            query = query.where(AgentRun.status == status)
        query = query.order_by(AgentRun.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()


class ToolCallRepository(BaseRepository[ToolCall]):
    def __init__(self, db: AsyncSession):
        super().__init__(ToolCall, db)

    async def list_by_run(self, agent_run_id: uuid.UUID) -> Sequence[ToolCall]:
        query = select(ToolCall).where(ToolCall.agent_run_id == agent_run_id).order_by(ToolCall.created_at.asc())
        result = await self.db.execute(query)
        return result.scalars().all()

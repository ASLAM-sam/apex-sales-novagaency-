from typing import List, Optional
from app.core.exceptions import NotFoundError
from app.repositories.agent_run import AgentRunRepository
from app.schemas.agent_run import AgentRun


class AgentRunService:
    def __init__(self, run_repo: Optional[AgentRunRepository] = None):
        self.run_repo = run_repo or AgentRunRepository()

    async def create_run(self, run: AgentRun) -> AgentRun:
        doc = run.model_dump(by_alias=True, exclude={"id"})
        created = await self.run_repo.create(doc)
        return AgentRun(**created)

    async def get_run(self, run_id: str) -> AgentRun:
        doc = await self.run_repo.get_by_id(run_id)
        if not doc:
            raise NotFoundError(f"Agent run with ID '{run_id}' not found.")
        return AgentRun(**doc)

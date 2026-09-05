from typing import List, Optional
from app.core.exceptions import NotFoundError
from app.repositories.ai_generation import AIGenerationRepository
from app.schemas.ai_generation import AIGeneration


class AIGenerationService:
    def __init__(self, gen_repo: Optional[AIGenerationRepository] = None):
        self.gen_repo = gen_repo or AIGenerationRepository()

    async def create_generation(self, gen: AIGeneration) -> AIGeneration:
        doc = gen.model_dump(by_alias=True, exclude={"id"})
        created = await self.gen_repo.create(doc)
        return AIGeneration(**created)

    async def get_generation(self, gen_id: str) -> AIGeneration:
        doc = await self.gen_repo.get_by_id(gen_id)
        if not doc:
            raise NotFoundError(f"AI generation record with ID '{gen_id}' not found.")
        return AIGeneration(**doc)

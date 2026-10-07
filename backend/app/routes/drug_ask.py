from fastapi import APIRouter, HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from starlette.concurrency import run_in_threadpool

from app.db.pharma.release_connection import (
    PharmaceuticalReleaseUnavailable,
)
from app.db.pharma.release_repository import (
    FrozenPharmaReleaseRepository,
)
from app.services.pharma.ask import (
    EvidenceRepository,
    answer_question,
    topic_for,
)


router = APIRouter(
    prefix="/api/drugs",
    tags=["Stored Ask Dav AI"],
)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=1,
        max_length=500,
    )

    @field_validator("question")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError(
                "Question cannot be blank"
            )

        return value.strip()


@router.post("/{product_id}/ask")
async def drug_ask(
    product_id: str,
    request: AskRequest,
):
    try:
        product = await run_in_threadpool(
            FrozenPharmaReleaseRepository().find_by_id,
            product_id,
        )

        if product is None:
            raise HTTPException(
                404,
                "Drug not found",
            )

        topic = topic_for(
            request.question
        )

        package = (
            await run_in_threadpool(
                EvidenceRepository().package,
                product_id,
                topic,
            )
            if topic
            else None
        )

        class Retrieved:
            def package(self, *args):
                return package

        return await answer_question(
            product_id,
            request.question,
            repository=Retrieved(),
        )

    except PharmaceuticalReleaseUnavailable as exc:
        raise HTTPException(
            503,
            (
                "Stored pharmaceutical release "
                "evidence is unavailable"
            ),
        ) from exc

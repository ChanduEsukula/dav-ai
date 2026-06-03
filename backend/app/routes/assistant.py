from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.assistant_service import AssistantRequestError, generate_assistant_response
from app.services.llm_provider import LLMProviderError


router = APIRouter(prefix="/api/v1/assistant", tags=["Ask DAV AI"])


@router.post("/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(
    assistant_request: AssistantChatRequest,
    request: Request,
) -> AssistantChatResponse:
    try:
        return await generate_assistant_response(assistant_request)
    except AssistantRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": str(exc),
                "code": "ASSISTANT_INVALID_CONTEXT",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "Ask DAV AI is unavailable because the assistant provider is not configured.",
                "code": "ASSISTANT_PROVIDER_UNAVAILABLE",
                "request_id": getattr(request.state, "request_id", None),
            },
        ) from exc

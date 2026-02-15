from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.session import StudySession
from app.models.conversation import ConversationMessage
from app.schemas.tutor import ChatRequest, ChatResponse, ChatHistoryResponse, MessageOut
from app.services.claude_tutor import tutor, TutorServiceError
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/tutor", tags=["tutor"])
limiter = Limiter(key_func=get_remote_address)

# Max messages to send to Claude as conversation history
MAX_HISTORY_MESSAGES = 50


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")
async def chat_with_tutor(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get or create session
    if chat_request.session_id:
        result = await db.execute(
            select(StudySession).where(
                StudySession.id == chat_request.session_id,
                StudySession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = StudySession(
            user_id=current_user.id, mode="chat", topic=chat_request.topic
        )
        db.add(session)
        await db.flush()

    # Load recent conversation history (capped to control cost and context window)
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session.id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
    )
    history_rows = list(reversed(result.scalars().all()))
    conversation_history = [
        {"role": m.role, "content": m.content} for m in history_rows
    ]

    # Call Claude
    try:
        response_text = await tutor.chat(chat_request.content, conversation_history)
    except TutorServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Save both messages
    user_msg = ConversationMessage(
        user_id=current_user.id,
        session_id=session.id,
        role="user",
        content=chat_request.content,
        topic=chat_request.topic,
    )
    assistant_msg = ConversationMessage(
        user_id=current_user.id,
        session_id=session.id,
        role="assistant",
        content=response_text,
        topic=chat_request.topic,
    )
    db.add_all([user_msg, assistant_msg])

    return ChatResponse(response=response_text, session_id=session.id)


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify session belongs to user
    result = await db.execute(
        select(StudySession).where(
            StudySession.id == session_id,
            StudySession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load messages
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.created_at)
    )
    messages = result.scalars().all()

    return ChatHistoryResponse(
        session_id=session_id,
        messages=[MessageOut.model_validate(m) for m in messages],
    )

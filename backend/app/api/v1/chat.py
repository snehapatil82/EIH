import time
import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database.connection import get_db
from app.models.repository import Repository
from app.models.chat import Conversation, Message
from app.schemas.chat import ChatRequest, ChatAnswerResponse, ConversationResponse, MessageResponse
from app.rag.retriever import RepositoryRetriever
from app.rag.citation_builder import CitationBuilder
from app.llm.provider import get_llm_provider
from app.core.logging import logger

router = APIRouter(tags=["AI Chat & Knowledge"])

retriever = RepositoryRetriever()
citation_builder = CitationBuilder()

@router.post("/repositories/{repository_id}/ask", response_model=ChatAnswerResponse)
async def ask_repository_question(
    repository_id: str,
    req: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    
    # Verify repository exists
    result = await db.execute(select(Repository).where(Repository.id == repository_id))
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get or create conversation
    conv_id = req.conversation_id
    if conv_id:
        conv_res = await db.execute(select(Conversation).where(Conversation.id == conv_id))
        conversation = conv_res.scalars().first()
    else:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            repository_id=repository_id,
            title=req.question[:60]
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # 1. Load recent conversation history for continuity (last 6 messages)
    history_messages = []
    if conv_id:
        from app.models.chat import Message as ChatMessage
        from sqlalchemy import select as sa_select
        hist_result = await db.execute(
            sa_select(ChatMessage)
            .where(ChatMessage.conversation_id == conv_id)
            .order_by(ChatMessage.created_at.asc())
        )
        past_msgs = hist_result.scalars().all()
        for m in past_msgs[-6:]:
            history_messages.append({"role": m.role, "content": m.content})

    # 2. Retrieve relevant codebase chunks (with multi-signal boosting & conversation context)
    retrieved_chunks = retriever.retrieve_context(
        repository_id,
        req.question,
        top_k=8,
        conversation_history=history_messages
    )

    # 3. Build explicit source citations
    citations = citation_builder.build_citations(retrieved_chunks)

    # 4. Generate grounded LLM response
    llm = get_llm_provider()
    system_prompt = (
        "You are a Senior Principal Software Architect and expert code analyst.\n\n"
        "You have been given retrieved source code chunks from the repository (provided below as context). "
        "Your job is to DIRECTLY answer the user's SPECIFIC question using ONLY that retrieved code. "
        "Do NOT give a generic architectural overview unless the question explicitly asks for one.\n\n"
        "Rules:\n"
        "1. ALWAYS start by restating what the user asked and mapping it to the most relevant retrieved file/function.\n"
        "2. Quote REAL code from the context chunks with file paths and line numbers.\n"
        "3. Walk through the code step-by-step to explain exactly what it does.\n"
        "4. Point out entities, parameters, return values, and side-effects.\n"
        "5. End with a 'For newcomers' section that explains the concept simply.\n\n"
        "Use Markdown: headings, code blocks (with language tag), bullet lists, and bold for key terms."
    )
    answer = await llm.generate_response(
        prompt=req.question,
        system_prompt=system_prompt,
        context_chunks=retrieved_chunks,
        conversation_history=history_messages
    )

    latency = round(time.time() - start_time, 3)

    # 4. Save messages in conversation history
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=req.question,
        citations=[]
    )
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        citations=citations
    )
    # Update conversation's updated_at timestamp
    conversation.updated_at = datetime.datetime.utcnow()
    db.add(conversation)
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()

    return ChatAnswerResponse(
        conversation_id=conversation.id,
        answer=answer,
        citations=citations,
        latency_seconds=latency,
        tokens_used=len(answer.split()) * 2
    )

@router.get("/repositories/{repository_id}/conversations", response_model=List[ConversationResponse])
async def list_conversations(repository_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.repository_id == repository_id)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return None

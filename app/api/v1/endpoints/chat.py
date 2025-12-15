from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.llm.conversation_service import conversation_service
from app.memory.manager import ChatMessage
import uuid

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    top_k: int = 3
    use_reranker: bool = True
    citation_mode: bool = True
    filters: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str

from fastapi.responses import StreamingResponse

@router.post("/message", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id or conversation_service.create_session()
    
    # Pack options
    options = {
        "model": request.model,
        "temperature": request.temperature,
        "top_k": request.top_k,
        "use_reranker": request.use_reranker,
        "citation_mode": request.citation_mode,
        "filters": request.filters
    }
    
    try:
        response_text = await conversation_service.chat(session_id, request.query, options)
        return ChatResponse(session_id=session_id, response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    session_id = request.session_id or conversation_service.create_session()
    
    options = {
        "model": request.model,
        "temperature": request.temperature,
        "top_k": request.top_k,
        "use_reranker": request.use_reranker,
        "citation_mode": request.citation_mode,
        "filters": request.filters
    }
    
    async def event_generator():
        # First yield session_id as a metadata event or header? 
        # For simplicity in this demo, we just stream content. 
        # But we need to return session_id to client. 
        # Strategy: Yield a JSON header first, then text? 
        # Or just stream text and rely on client having session_id or getting it via header.
        # Let's send session_id in a custom header.
        try:
            async for chunk in conversation_service.chat_stream(session_id, request.query, options):
                if isinstance(chunk, dict):
                    import json
                    yield json.dumps(chunk) + "\n"
                else:
                    import json
                    yield json.dumps({"content": chunk}) + "\n"
        except Exception as e:
            import json
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(
        event_generator(), 
        media_type="text/plain",
        headers={"X-Session-ID": session_id}
    )

@router.get("/history/{session_id}", response_model=List[ChatMessage])
async def get_history(session_id: str):
    history = conversation_service.memory_manager.get_history(session_id)
    if not history and session_id not in conversation_service.memory_manager._store:
         raise HTTPException(status_code=404, detail="Session not found")
    return history

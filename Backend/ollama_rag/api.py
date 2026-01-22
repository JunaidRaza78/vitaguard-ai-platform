from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging, json, uuid

try:
    from .rag_chatbot import get_chatbot
    from .ollama_client import get_ollama_client
except ImportError:
    from rag_chatbot import get_chatbot
    from ollama_client import get_ollama_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Medical RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------
class ChatRequest(BaseModel):
    message: str | None = None
    question: str | None = None
    conversation_id: str | None = None
    user_id: str | None = None
    specialty: str | None = None
    top_k: int = 5
    temperature: float = 0.3
    stream: bool = False

class EmbeddingRequest(BaseModel):
    text: str

# -------------------------------------------------
# CHAT
# -------------------------------------------------
@app.post("/chat")
async def chat(req: ChatRequest):
    text = (req.message or req.question or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    chatbot = get_chatbot()
    conv_id = req.conversation_id or str(uuid.uuid4())

    if req.stream:
        async def stream():
            for chunk in chatbot.chat(
                question=text,
                conversation_id=conv_id,
                user_id=req.user_id,
                specialty=req.specialty,
                top_k=req.top_k,
                temperature=req.temperature,
                stream=True
            ):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    result = chatbot.chat(
        question=text,
        conversation_id=conv_id,
        user_id=req.user_id,
        specialty=req.specialty,
        top_k=req.top_k,
        temperature=req.temperature,
        stream=False
    )

    return {
        "status": "success",
        "conversation_id": conv_id,
        "answer": result.get("answer"),
        "sources": result.get("sources", []),
        "context_used": result.get("context_used", False),
        "storage": result.get("storage")
    }

# -------------------------------------------------
# EMBEDDINGS (READ-ONLY)
# -------------------------------------------------
@app.post("/embeddings/generate")
def generate_embedding(req: EmbeddingRequest):
    from query_by_agent import model
    return {
        "dimensions": len(model.encode(req.text)),
        "embedding": model.encode(req.text).tolist()
    }

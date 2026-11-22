from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.rag.retriever import rag_retriever
from backend.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler:
    1. Ensures SQLite tables are initialized.
    2. Primes and verifies ChromaDB knowledge base index.
    """
    print("[STARTUP] Initializing database schema...")
    init_db()

    print("[STARTUP] Checking hospital document vector index...")
    try:
        count = rag_retriever.load_and_index_documents(force_reload=False)
        print(f"[STARTUP] ChromaDB RAG index verified: {count} chunks active.")
    except Exception as e:
        print(f"[STARTUP WARNING] RAG vector indexing error: {e}")

    yield

    print("[SHUTDOWN] Hospital Intake Assistant shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Hospital Patient Intake and Department Routing Assistant using Microsoft Semantic Kernel and ChromaDB RAG.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for Vite frontend and local requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)

@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "docs_url": "/docs",
        "api_health": "/api/health",
        "disclaimer": settings.MANDATORY_DISCLAIMER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

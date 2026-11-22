import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from backend.main import app
from backend.database import init_db
from backend.rag.retriever import rag_retriever

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Initializes database and ensures RAG documents are indexed before running tests."""
    init_db()
    rag_retriever.load_and_index_documents(force_reload=False)

@pytest.fixture
def client():
    """Provides a FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Hospital Patient Intake and Department Routing Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # SQLite database URL
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/hospital_intake.db"

    # RAG settings
    DOCUMENTS_DIR: str = str(BASE_DIR / "documents" / "hospital_info")
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_db")

    # Logging
    EXECUTION_LOG_PATH: str = str(BASE_DIR / "logs" / "agent_runs.jsonl")

    # Disclaimer constant
    MANDATORY_DISCLAIMER: str = (
        "IMPORTANT NOTICE: This is an intake routing and information assistant, NOT a medical diagnosis system. "
        "It does not diagnose conditions, prescribe medications, or replace clinical consultation. "
        "Always consult a qualified healthcare professional for medical evaluation."
    )

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

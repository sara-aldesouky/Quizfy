"""
Configuration and environment variable handling for Performance Analytics service.
Includes startup validation to ensure all required keys are present.
"""

import os
from dotenv import load_dotenv

# Load environment variables from the local process environment.
load_dotenv()


class Config:
    """Production-grade configuration management."""
    
    # Environment
    ENV = os.getenv("ENV", "development")
    DEBUG = ENV == "development"
    
    # API Keys & External Services
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    
    # Vector Database Configuration
    VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Analysis Parameters
    MIN_STUDENTS_AFFECTED = int(os.getenv("MIN_STUDENTS_AFFECTED", "2"))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
    MIN_EVIDENCE_QUESTIONS = int(os.getenv("MIN_EVIDENCE_QUESTIONS", "2"))
    
    # Performance Tuning
    PDF_BATCH_SIZE = int(os.getenv("PDF_BATCH_SIZE", "10"))
    LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "5"))
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "./logs/performance_analytics.log")
    
    # Database (optional, for persistence)
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./performance_analytics.db"
    )
    
    @classmethod
    def validate_startup(cls) -> None:
        """
        Validate that all required environment variables are set.
        Called at application startup to fail fast on missing config.
        """
        required_vars = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        }
        
        missing_vars = [key for key, value in required_vars.items() if not value]
        
        if missing_vars:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please set them securely in the backend runtime environment."
            )
        
        # Validate model choice
        valid_prefixes = ("gpt-", "o")
        if not cls.OPENAI_MODEL.startswith(valid_prefixes):
            raise ValueError(
                "OPENAI_MODEL must be an OpenAI chat-capable model name, "
                f"got: {cls.OPENAI_MODEL}"
            )
        
        # Validate vector DB choice
        valid_db_types = ["chroma"]
        if cls.VECTOR_DB_TYPE not in valid_db_types:
            raise ValueError(
                f"VECTOR_DB_TYPE must be one of {valid_db_types}, "
                f"got: {cls.VECTOR_DB_TYPE}"
            )
        
        # Ensure upload directory exists
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
        os.makedirs(cls.VECTOR_DB_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE) or ".", exist_ok=True)

    @classmethod
    def require_openai_api_key(cls) -> str:
        """Return the configured API key or fail without exposing secret values."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        return api_key


# Create config instance
config = Config()

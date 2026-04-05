import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:////Users/jackyfox/New_Smart_Agent_Harness_System/backend/agent_harness.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    MODEL_ID = os.getenv("MODEL_ID", "claude-3-5-sonnet-20241022")

    # Worktree
    WORKTREE_BASE_PATH = os.getenv(
        "WORKTREE_BASE_PATH",
        "/Users/jackyfox/New_Smart_Agent_Harness_System/.worktrees",
    )

    # Agent settings
    MAX_CONCURRENT_EXECUTORS = 10
    TASK_TIMEOUT_SECONDS = 300
    WORKTREE_GIT_TIMEOUT = 120
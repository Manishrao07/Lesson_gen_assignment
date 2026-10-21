import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env if present
load_dotenv()

class Settings:
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    
    # Free-tier API keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Models
    GEN_MODEL: str = os.getenv("GEN_MODEL", "gemini-flash-latest")
    JUDGE_MODEL: str = os.getenv("JUDGE_MODEL", "qwen/qwen3.8-27b")
    
    # Ollama Fallback
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # Execution & Free-tier safeguards
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
    CACHE_DIR: Path = PROJECT_ROOT / os.getenv("CACHE_DIR", ".cache/llm")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
    RATE_LIMIT_DELAY_SECONDS: float = float(os.getenv("RATE_LIMIT_DELAY_SECONDS", "0.5"))
    
    # Knowledge & Rubric paths
    GROUNDING_PATH: Path = PROJECT_ROOT / "knowledge" / "rag_facts.md"
    RUBRIC_PATH: Path = PROJECT_ROOT / "rubric" / "rubric.yaml"
    MEMORY_RUNS_PATH: Path = PROJECT_ROOT / "memory" / "runs.jsonl"
    LEARNED_RULES_PATH: Path = PROJECT_ROOT / "memory" / "learned_rules.json"
    OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"

settings = Settings()

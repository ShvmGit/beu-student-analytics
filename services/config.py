from pydantic_settings import BaseSettings
from pydantic import Field
from loguru import logger
import sys


class Settings(BaseSettings):
    # Groq
    groq_api_key: str

    # BEU API
    beu_api_base_url: str = "https://beu-bih.ac.in/backend/v1"

    # Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600
    use_redis: bool = False  # Phase 1: False

    # Retry
    max_retries: int = 3
    retry_delay_seconds: int = 2

    # Logging
    log_level: str = "INFO"

    # Models
    model_chat: str = "llama-3.1-8b-instant"
    model_analysis: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    model_fallback: str = "qwen/qwen3-32b"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Singleton
settings = Settings()


def setup_logging(level: str = "INFO"):
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        serialize=False,
    )

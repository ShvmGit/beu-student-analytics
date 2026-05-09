from services.config import settings
from services.groq_client import GroqClient
from loguru import logger

TASK_MODEL_MAP = {
    "chat":        settings.model_chat,      # llama-3.1-8b-instant
    "analysis":    settings.model_analysis,  # llama-4-scout-17b-16e-instruct
    "explanation": settings.model_chat,      # llama-3.1-8b-instant
    "fallback":    settings.model_fallback,  # qwen/qwen3-32b
}

MODEL_PARAMS = {
    "chat": {
        "temperature": 0.7,
        "max_tokens": 512,
    },
    "analysis": {
        "temperature": 0.1,
        "max_tokens": 1024,
    },
    "explanation": {
        "temperature": 0.6,
        "max_tokens": 512,
    },
}

# Singleton client — reused across all calls to avoid connection overhead
_groq_client: GroqClient | None = None


def _get_client() -> GroqClient:
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient(settings.groq_api_key)
    return _groq_client


class ModelUnavailableError(Exception):
    pass


async def route_completion(
    task_type: str,
    messages: list[dict],
    **kwargs,
) -> str:
    """
    1. Select primary model for task_type
    2. Attempt completion
    3. On RateLimitError or failure: try fallback model
    4. On fallback failure: try last resort or raise ModelUnavailableError
    """
    primary_model = TASK_MODEL_MAP.get(task_type, settings.model_chat)
    fallback_model = TASK_MODEL_MAP["fallback"]
    last_resort_model = TASK_MODEL_MAP["chat"]

    params = MODEL_PARAMS.get(task_type, {"temperature": 0.5, "max_tokens": 512})
    client = _get_client()

    models_to_try = [primary_model]
    if fallback_model != primary_model:
        models_to_try.append(fallback_model)
    if last_resort_model not in models_to_try:
        models_to_try.append(last_resort_model)

    for model in models_to_try:
        try:
            logger.info(f"Model selected: task={task_type}, model={model}")
            return await client.complete(
                model=model,
                messages=messages,
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                **kwargs,
            )
        except Exception as e:
            logger.warning(f"Failed with model {model}: {e}")

    logger.error(f"All models failed for task: {task_type}")
    raise ModelUnavailableError(
        "The AI models are currently unavailable. Please try again later."
    )

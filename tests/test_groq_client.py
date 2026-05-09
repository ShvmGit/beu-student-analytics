import pytest
from services.groq_client import GroqClient
from services.config import settings

@pytest.mark.asyncio
async def test_basic_completion():
    # Only run if real API key is set, otherwise skip
    if "your_groq_api_key_here" in settings.groq_api_key:
        pytest.skip("No real Groq API key set")
        
    client = GroqClient(settings.groq_api_key)
    try:
        result = await client.complete(
            model=settings.model_chat,
            messages=[{"role": "user", "content": "Reply with just the word: HELLO"}],
            max_tokens=10
        )
        assert "HELLO" in result.upper()
    except Exception as e:
        pytest.fail(f"API call failed: {e}")

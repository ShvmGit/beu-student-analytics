from groq import AsyncGroq, RateLimitError, APIStatusError, AuthenticationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type
from loguru import logger
import time

class GroqClient:
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(min=1, max=8),
        retry=retry_if_not_exception_type(AuthenticationError)
    )
    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        response_format: dict | None = None,
    ) -> str:
        """
        Calls Groq chat completions.
        Returns the content string of the first choice.
        On RateLimitError: raises so tenacity can retry.
        On AuthenticationError: raises immediately (do not retry).
        Logs model used, token estimate, and latency.
        """
        start_time = time.time()
        logger.debug(f"Calling Groq model {model}...")
        
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format
                
            response = await self.client.chat.completions.create(**kwargs)
            
            latency = time.time() - start_time
            logger.info(f"Groq API call to {model} completed in {latency:.2f}s")
            
            return response.choices[0].message.content
            
        except RateLimitError as e:
            logger.warning(f"Rate limited by Groq API on model {model}. Retrying...")
            raise e
        except AuthenticationError as e:
            logger.error("Authentication Error: Check your GROQ_API_KEY")
            raise e
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise e

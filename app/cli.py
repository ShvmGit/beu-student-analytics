import asyncio
import sys
import os

# Add root project dir to path so we can import packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from agents.chat_agent import ChatAgent
from schemas.agent_schema import AgentContext
from services.config import setup_logging
import uuid

async def run_cli():
    setup_logging("INFO")
    context = AgentContext(session_id=str(uuid.uuid4()))
    agent = ChatAgent()

    print("=== BEU Result Intelligence Assistant ===")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        response = await agent.handle_message(user_input, context)
        print(f"Assistant: {response}\n")

if __name__ == "__main__":
    asyncio.run(run_cli())

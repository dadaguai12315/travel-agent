"""
LLM Client — OpenAI-compatible interface for DeepSeek/Claude/GPT.
"""

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.agent.tools import ALL_TOOL_SCHEMAS, search_enabled
from app.core.config import settings
from app.core.llm_prompts import SYSTEM_PROMPT_NO_SEARCH, SYSTEM_PROMPT_WITH_SEARCH

_client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    timeout=120.0,
    max_retries=1,
)


def get_system_prompt() -> str:
    return SYSTEM_PROMPT_WITH_SEARCH if search_enabled() else SYSTEM_PROMPT_NO_SEARCH


def get_tools() -> list[dict] | None:
    return ALL_TOOL_SCHEMAS if search_enabled() else None


async def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
) -> dict:
    """Non-streaming chat completion. Returns the full message dict.

    Used for: tool-calling rounds in the agent workflow.
    """
    kwargs: dict = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.7,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await _client.chat.completions.create(**kwargs)
    choice = response.choices[0]
    return choice.message.model_dump()


async def chat_completion_stream(
    messages: list[dict],
) -> AsyncIterator[str]:
    """Streaming chat completion. Yields content text tokens.

    Client timeout is 120s. Client disconnection triggers CancelledError.
    """
    stream = await _client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.7,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content

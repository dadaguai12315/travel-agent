from openai import AsyncOpenAI

from app.config import settings

_client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
)


async def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
) -> dict:
    """Non-streaming chat completion. Returns the full message dict."""
    kwargs = {
        "model": settings.deepseek_model,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    response = await _client.chat.completions.create(**kwargs)
    choice = response.choices[0]
    return choice.message.model_dump()


async def chat_completion_stream(
    messages: list[dict],
) -> "AsyncIterator[str]":
    """Streaming chat completion. Yields content token strings."""
    stream = await _client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content

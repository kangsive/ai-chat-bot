import asyncio
from typing import Any, Dict, List, AsyncGenerator, Optional

from app.core.config import settings


async def generate_llm_response(
    messages: List[Dict[str, str]],
    model: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generate a response from the LLM.
    
    This is a mock implementation that simulates a streaming LLM response.
    In a real application, this would integrate with an actual LLM API.
    
    Args:
        messages: A list of message dictionaries with 'role' and 'content'
        model: Optional model name to use for generation (defaults to settings.LLM_MODEL)
        
    Yields:
        Tokens of the generated response
    """
    # Use the provided model or fall back to default
    model_to_use = model or settings.LLM_MODEL
    
    # Simple mock response generator
    # In a real app, replace with actual LLM API call
    
    # For a real implementation, you might use something like:
    # async with httpx.AsyncClient() as client:
    #     async with client.stream(
    #         "POST",
    #         "https://api.openai.com/v1/chat/completions",
    #         headers={
    #             "Authorization": f"Bearer {settings.LLM_API_KEY}",
    #             "Content-Type": "application/json"
    #         },
    #         json={
    #             "model": model_to_use,
    #             "messages": messages,
    #             "stream": True
    #         },
    #         timeout=60.0
    #     ) as response:
    #         async for chunk in response.aiter_lines():
    #             if chunk.startswith("data: "):
    #                 # Process streaming response data
    #                 # ...
    #                 yield token
    
    # Mock response
    response_text = f"This is a simulated response from the AI using model: {model_to_use}. In a real implementation, this would be an actual response from an LLM API like OpenAI, Anthropic, or a local model."
    
    # Get the last user message for context in our mock response
    last_message = next((m for m in reversed(messages) if m["role"] == "user"), None)
    if last_message:
        if isinstance(last_message['content'], list):
            last_message_content = last_message['content'][0]['text']
        else:
            last_message_content = last_message['content']
        response_text += f"\n\nYou asked: {last_message_content[:30]}..."
    
    # Simulate streaming by yielding parts of the response with delays
    words = response_text.split()
    for i in range(0, len(words), 3):
        chunk = " ".join(words[i:i+3]) + " "
        yield chunk
        await asyncio.sleep(0.1)  # Simulate thinking 
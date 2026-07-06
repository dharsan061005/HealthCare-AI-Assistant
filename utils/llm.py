"""
LLM utility for Healthcare AI Assistant.
Wraps Groq (groq SDK) with graceful error handling and fallback messages.
"""

import logging
from typing import List, Dict, Optional

import config  # loads .env automatically

logger = logging.getLogger(__name__)


def _get_client():
    """
    Lazily build a Groq client instance.
    Raises RuntimeError if the package is missing or the API key is not set.
    """
    try:
        from groq import Groq
    except ImportError as e:
        raise RuntimeError(
            "groq package is not installed. "
            "Run: pip install groq"
        ) from e

    api_key = config.GROQ_API_KEY
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file:\n"
            "  GROQ_API_KEY=your-key-here"
        )

    from groq import Groq
    return Groq(api_key=api_key)


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    """
    Call Groq chat completions and return the reply as a string.

    Accepts OpenAI-style messages (role: system/user/assistant) — no conversion needed
    since Groq's API is OpenAI-compatible.

    Args:
        messages:    List of {'role': 'system'|'user'|'assistant', 'content': ...}.
        model:       Override config model (default: GROQ_MODEL from config).
        max_tokens:  Max output tokens.
        temperature: Response creativity 0-1.

    Returns:
        The assistant reply text, or a user-friendly error string on failure.
    """
    _model_name = model or config.GROQ_MODEL
    _max_tokens = max_tokens or config.GROQ_MAX_TOKENS
    _temperature = temperature if temperature is not None else config.GROQ_TEMPERATURE

    try:
        client = _get_client()

        response = client.chat.completions.create(
            model=_model_name,
            messages=messages,
            max_tokens=_max_tokens,
            temperature=_temperature,
        )

        reply = response.choices[0].message.content

        logger.info(
            "Groq call successful. Model=%s, reply_length=%d chars",
            _model_name, len(reply) if reply else 0,
        )
        return reply.strip() if reply else "No response generated."

    except RuntimeError as e:
        logger.warning("LLM configuration error: %s", e)
        return f"⚠️ **LLM Unavailable:** {e}"

    except Exception as e:
        error_str = str(e)
        logger.error("Groq API call failed: %s", error_str)

        if "api_key" in error_str.lower() or "api key" in error_str.lower() or "invalid" in error_str.lower() or "auth" in error_str.lower():
            return (
                "⚠️ **Authentication Error:** Your Groq API key appears to be invalid. "
                "Please check your .env file."
            )
        if "quota" in error_str.lower() or "rate_limit" in error_str.lower() or "429" in error_str:
            return (
                "⚠️ **Rate Limit Exceeded:** You have exceeded your Groq API quota. "
                "Please wait a moment and try again."
            )
        if "model" in error_str.lower() and ("not found" in error_str.lower() or "does not exist" in error_str.lower()):
            return (
                f"⚠️ **Model Not Found:** The model '{_model_name}' is not available. "
                "Check GROQ_MODEL in your .env file."
            )
        return (
            f"⚠️ **LLM Error:** Unable to get a response from Groq. "
            f"Details: {error_str[:200]}"
        )


def simple_query(system_prompt: str, user_message: str) -> str:
    """
    Convenience wrapper for a single system + user message exchange.

    Args:
        system_prompt: The system context/instructions.
        user_message:  The user's query.

    Returns:
        The assistant's reply string.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return chat_completion(messages)

"""
LLM utility for Healthcare AI Assistant.
Supports two providers:
  - Groq  (default): llama-3.3-70b-versatile via groq SDK
  - Gemini          : gemini-1.5-flash via google-generativeai SDK

Provider is selected by AI_PROVIDER in .env ("groq" | "gemini").
Falls back to Groq if Gemini key is missing.
"""

import logging
from typing import List, Dict, Optional

import config  # loads .env automatically

logger = logging.getLogger(__name__)


# ─── Groq ─────────────────────────────────────────────────────────────────────

def _get_groq_client():
    """Lazily build a Groq client. Raises RuntimeError on missing deps/key."""
    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError("groq package not installed. Run: pip install groq") from exc
    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file:\n  GROQ_API_KEY=your-key-here"
        )
    return Groq(api_key=config.GROQ_API_KEY)


def _groq_chat(
    messages: List[Dict[str, str]],
    model: Optional[str],
    max_tokens: Optional[int],
    temperature: Optional[float],
) -> str:
    """
    Call Groq chat completions.

    Args:
        messages:    OpenAI-style list of {'role': ..., 'content': ...}.
        model:       Model override; defaults to config.GROQ_MODEL.
        max_tokens:  Max output tokens.
        temperature: Sampling temperature.

    Returns:
        Assistant reply string, or a user-friendly error string.
    """
    _model       = model       or config.GROQ_MODEL
    _max_tokens  = max_tokens  or config.GROQ_MAX_TOKENS
    _temperature = temperature if temperature is not None else config.GROQ_TEMPERATURE

    try:
        client   = _get_groq_client()
        response = client.chat.completions.create(
            model=_model,
            messages=messages,
            max_tokens=_max_tokens,
            temperature=_temperature,
        )
        reply = response.choices[0].message.content
        logger.info("Groq OK — model=%s, chars=%d", _model, len(reply or ""))
        return reply.strip() if reply else "No response generated."

    except RuntimeError as exc:
        logger.warning("Groq config error: %s", exc)
        return f"⚠️ **LLM Unavailable:** {exc}"
    except Exception as exc:
        return _handle_api_error(exc, "Groq", _model)


# ─── Gemini ───────────────────────────────────────────────────────────────────

def _get_gemini_model(model_name: str):
    """
    Lazily configure and return a Gemini GenerativeModel instance.
    Raises RuntimeError on missing deps/key.
    """
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai not installed. Run: pip install google-generativeai"
        ) from exc
    if not config.GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file:\n  GEMINI_API_KEY=your-key-here"
        )
    genai.configure(api_key=config.GEMINI_API_KEY)
    return genai.GenerativeModel(model_name)


def _openai_to_gemini(messages: List[Dict[str, str]]) -> tuple:
    """
    Convert OpenAI-style messages to Gemini format.

    Gemini uses 'user'/'model' roles and a flat history list.
    System messages are prepended to the first user message.

    Returns:
        (system_instruction, gemini_history, last_user_message)
    """
    system_parts = []
    history      = []
    last_user    = ""

    for msg in messages:
        role    = msg["role"]
        content = msg["content"]
        if role == "system":
            system_parts.append(content)
        elif role == "user":
            last_user = content
            if history or not system_parts:
                history.append({"role": "user", "parts": [content]})
        elif role == "assistant":
            history.append({"role": "model", "parts": [content]})

    # If we only have one user message (no prior history), return it as the prompt
    if len(history) == 1 and history[0]["role"] == "user":
        history = []

    system_instruction = "\n\n".join(system_parts) if system_parts else None
    return system_instruction, history, last_user


def _gemini_chat(
    messages: List[Dict[str, str]],
    model: Optional[str],
    max_tokens: Optional[int],
    temperature: Optional[float],
) -> str:
    """
    Call Gemini chat completions.

    Args:
        messages:    OpenAI-style list of {'role': ..., 'content': ...}.
        model:       Model override; defaults to config.GEMINI_MODEL.
        max_tokens:  Max output tokens (mapped to max_output_tokens).
        temperature: Sampling temperature.

    Returns:
        Assistant reply string, or a user-friendly error string.
    """
    import google.generativeai as genai

    _model       = model      or config.GEMINI_MODEL
    _max_tokens  = max_tokens or config.GROQ_MAX_TOKENS   # reuse config value
    _temperature = temperature if temperature is not None else config.GROQ_TEMPERATURE

    try:
        gen_model = _get_gemini_model(_model)
        system_instruction, history, last_user = _openai_to_gemini(messages)

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=_max_tokens,
            temperature=_temperature,
        )

        if history:
            chat    = gen_model.start_chat(history=history)
            resp    = chat.send_message(last_user, generation_config=generation_config)
        else:
            # Single-turn with optional system prefix
            prompt = f"{system_instruction}\n\n{last_user}" if system_instruction else last_user
            resp   = gen_model.generate_content(prompt, generation_config=generation_config)

        reply = resp.text if hasattr(resp, "text") else str(resp)
        logger.info("Gemini OK — model=%s, chars=%d", _model, len(reply or ""))
        return reply.strip() if reply else "No response generated."

    except RuntimeError as exc:
        logger.warning("Gemini config error: %s", exc)
        return f"⚠️ **LLM Unavailable:** {exc}"
    except Exception as exc:
        return _handle_api_error(exc, "Gemini", _model)


# ─── Shared error handler ────────────────────────────────────────────────────

def _handle_api_error(exc: Exception, provider: str, model: str) -> str:
    """Translate common API exceptions into readable user messages."""
    err = str(exc).lower()
    logger.error("%s API error: %s", provider, exc)

    if any(k in err for k in ("api_key", "api key", "invalid", "auth", "credentials")):
        return (
            f"⚠️ **Authentication Error:** Your {provider} API key appears to be invalid. "
            f"Please check your .env file."
        )
    if any(k in err for k in ("quota", "rate_limit", "429", "resource_exhausted")):
        return (
            f"⚠️ **Rate Limit:** {provider} quota exceeded. Please wait a moment and try again."
        )
    if "not found" in err or "does not exist" in err:
        return (
            f"⚠️ **Model Not Found:** '{model}' is unavailable on {provider}. "
            f"Check your model setting in .env."
        )
    return (
        f"⚠️ **{provider} Error:** Unable to get a response. "
        f"Details: {str(exc)[:250]}"
    )


# ─── Public API ───────────────────────────────────────────────────────────────

def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
) -> str:
    """
    Unified chat completion entry point.

    Selects provider based on:
      1. Explicit `provider` argument ("groq" | "gemini")
      2. AI_PROVIDER env var
      3. Falls back to Groq if Gemini key is absent

    Args:
        messages:    OpenAI-style [{'role': 'system'|'user'|'assistant', 'content': ...}].
        model:       Override the default model for the selected provider.
        max_tokens:  Max output tokens.
        temperature: Response creativity (0–1).
        provider:    Force a specific provider ("groq" | "gemini").

    Returns:
        The assistant reply as a plain string.
    """
    _provider = (provider or config.AI_PROVIDER or "groq").lower()

    # Auto-downgrade to Groq if Gemini key is not set
    if _provider == "gemini" and not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — falling back to Groq.")
        _provider = "groq"

    if _provider == "gemini":
        return _gemini_chat(messages, model, max_tokens, temperature)
    else:
        return _groq_chat(messages, model, max_tokens, temperature)


def simple_query(system_prompt: str, user_message: str, provider: Optional[str] = None) -> str:
    """
    Convenience wrapper for a single system + user message exchange.

    Args:
        system_prompt: The system context / instructions.
        user_message:  The user's query.
        provider:      Optional provider override ("groq" | "gemini").

    Returns:
        The assistant reply string.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]
    return chat_completion(messages, provider=provider)


def get_active_provider() -> str:
    """Return the currently active provider label for display in the UI."""
    p = (config.AI_PROVIDER or "groq").lower()
    if p == "gemini" and config.GEMINI_API_KEY:
        return "Gemini"
    return "Groq"

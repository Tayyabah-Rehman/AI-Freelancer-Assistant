"""
Shared AI integration layer.

Every AI-powered module (Proposals, Cover Letters, and later Gig
Descriptions, Pricing, Client Replies) calls into this file so the Groq
API key, model name, error handling, and credit deduction logic only
live in one place.
"""

import re
import requests
from flask import current_app
from extensions import db

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class AIGenerationError(Exception):
    """Raised whenever the AI provider can't return usable content."""
    pass


def call_groq(system_prompt, user_prompt, max_tokens=900, temperature=0.7, api_key_override=None):
    """
    Sends a chat-completion request to Groq and returns the generated text.
    Raises AIGenerationError with a user-friendly message on any failure.

    api_key_override: if a user has set their own key in Settings, pass it
    here so it's used instead of the app-wide GROQ_API_KEY from .env.
    """
    api_key = api_key_override or current_app.config.get("GROQ_API_KEY")
    model = current_app.config.get("GROQ_MODEL")

    if not api_key:
        raise AIGenerationError(
            "No Groq API key configured. Add one in Settings, or set GROQ_API_KEY in your .env file and restart the app."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        raise AIGenerationError("The AI provider took too long to respond. Please try again.")
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        raise AIGenerationError(f"AI provider returned an error (status {status}). Check your GROQ_API_KEY.")
    except requests.exceptions.RequestException as e:
        raise AIGenerationError(f"Could not reach the AI provider: {e}")
    except (KeyError, IndexError, ValueError):
        raise AIGenerationError("Received an unexpected response format from the AI provider.")


def user_api_key(user):
    """Returns the user's personal Groq key from Settings, or None to fall back to .env."""
    if user and user.profile and user.profile.groq_api_key:
        return user.profile.groq_api_key
    return None


def has_credits(user):
    return bool(user.ai_credits and user.ai_credits > 0)


def deduct_credit(user):
    """Deducts 1 AI credit. Does not commit - caller commits alongside their own changes."""
    if user.ai_credits and user.ai_credits > 0:
        user.ai_credits -= 1
    db.session.add(user)


def parse_ai_sections(text, keys):
    """
    Parses an AI response that uses '### SECTION_NAME' markers into a dict.

    Used by modules that need more than one field back from a single AI call
    (e.g. Gig Description needs description + SEO keywords + FAQs; Pricing
    needs delivery time + market analysis + improvement tips).

    keys: list of exact marker names, e.g. ['DESCRIPTION', 'SEO_KEYWORDS', 'FAQS']
    Returns dict {key: content}. If no markers are found at all, the entire
    response is placed under keys[0] and the rest are left empty, so nothing
    ever silently disappears even if the AI ignores the format.
    """
    pattern = re.compile(r"###\s*(" + "|".join(re.escape(k) for k in keys) + r")\s*\n", re.IGNORECASE)
    parts = pattern.split(text)

    result = {k: "" for k in keys}

    if len(parts) < 3:
        result[keys[0]] = text.strip()
        return result

    it = iter(parts[1:])
    for marker, content in zip(it, it):
        matched_key = next((k for k in keys if k.lower() == marker.lower()), None)
        if matched_key:
            result[matched_key] = content.strip()

    return result

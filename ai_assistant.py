"""
AI is a thin, OPTIONAL layer on top of the app - never persistent storage.
Flow: APPLICATION -> AI -> estimate/suggestion -> USER CONFIRMS -> DATABASE.

Uses Groq's OpenAI-compatible API if GROQ_API_KEY is set (env var or entered
in Settings). If no key is configured, every function here returns
ai_available=False and the UI falls back to non-AI behaviour - the rest of
the app works fully without this file doing anything.
"""
import os
import json

try:
    from groq import Groq
    _GROQ_INSTALLED = True
except ImportError:
    _GROQ_INSTALLED = False


def _get_client(api_key: str | None):
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key or not _GROQ_INSTALLED:
        return None
    try:
        return Groq(api_key=key)
    except Exception:
        return None


def ai_available(api_key: str | None) -> bool:
    return _get_client(api_key) is not None


def analyze_meal_text(description: str, api_key: str | None = None) -> dict:
    """Estimate calories/protein/carbs/fat from a free-text meal description.
    Returns {'ok': bool, 'error': str|None, 'estimate': {...}|None}."""
    client = _get_client(api_key)
    if not client:
        return {"ok": False, "error": "AI not configured (no Groq API key).", "estimate": None}

    prompt = (
        "Estimate total nutrition for this meal. Respond ONLY with JSON, no prose, "
        'in the exact form {"calories": number, "protein": number, "carbs": number, '
        f'"fat": number}}.\nMeal: {description}'
    )
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return {"ok": True, "error": None, "estimate": data}
    except Exception as e:
        return {"ok": False, "error": f"AI estimate failed: {e}", "estimate": None}


def ask_assistant(question: str, context: dict, api_key: str | None = None) -> dict:
    """General fitness Q&A grounded in the user's live stats (context dict)."""
    client = _get_client(api_key)
    if not client:
        return {"ok": False, "error": "AI not configured (no Groq API key).", "answer": None}

    system = (
        "You are a concise fitness & nutrition assistant inside a tracker app. "
        "Use the user's stats below when relevant. Keep answers short and practical. "
        "Never claim to store or remember anything - the app's database does that.\n"
        f"User stats: {json.dumps(context)}"
    )
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
            max_tokens=400,
        )
        return {"ok": True, "error": None, "answer": resp.choices[0].message.content.strip()}
    except Exception as e:
        return {"ok": False, "error": f"AI request failed: {e}", "answer": None}


def suggest_meal(calories_remaining, protein_remaining, goal, food_db, api_key: str | None = None):
    """Non-AI fallback always works: pick foods from the local DB that fit the
    remaining budget. If AI is configured, ask it to phrase a nicer suggestion."""
    candidates = [
        f for f in food_db
        if f["calories"] <= max(calories_remaining, 0) + 100 and f["protein"] >= min(protein_remaining, 20) * 0.3
    ]
    candidates = sorted(candidates, key=lambda f: -f["protein"])[:5]

    client = _get_client(api_key)
    if not client or not candidates:
        return {"ok": True, "ai_used": False, "candidates": candidates, "text": None}

    prompt = (
        f"Calories remaining today: {calories_remaining}. Protein remaining: {protein_remaining}g. "
        f"Goal: {goal}. From this food list, suggest ONE combination that fits (brief, 2 sentences max): "
        f"{json.dumps(candidates)}"
    )
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )
        return {"ok": True, "ai_used": True, "candidates": candidates, "text": resp.choices[0].message.content.strip()}
    except Exception:
        return {"ok": True, "ai_used": False, "candidates": candidates, "text": None}

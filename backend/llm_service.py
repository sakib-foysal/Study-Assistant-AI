import os
import json
import logging
import re
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

# Prefer requests for HTTP; if not installed, raise clear error at call time
try:
    import requests
except Exception:  # pragma: no cover - runtime fallback
    requests = None

# initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_api_key() -> Optional[str]:
    # Try common env names
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")


def _call_gemini(prompt: str, model: str = None, temperature: float = 0.2, max_output_tokens: int = 512) -> str:
    """Call Google's Generative Language (Gemini) REST endpoint using an API key.

    This function is defensive about response shapes and logs raw responses for debugging.
    It expects an environment variable `GEMINI_API_KEY` or `GOOGLE_API_KEY` to be set.
    """
    if requests is None:
        raise RuntimeError("The 'requests' package is required to use the Gemini adapter. Please install it (pip install requests).")

    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Missing Gemini API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment or .env file.")

    # Default Gemini-like model path; allow override via env
    model = model or os.getenv("GEMINI_MODEL") or "models/gemini-1.0"

    url = f"https://generativelanguage.googleapis.com/v1beta2/{model}:generate?key={api_key}"

    payload = {
        # modern GL API accepts prompt object; include commonly accepted fields
        "prompt": {"text": prompt},
        "temperature": temperature,
        "maxOutputTokens": max_output_tokens,
        # include alternate snake_case just in case server expects it
        "max_output_tokens": max_output_tokens,
    }

    logger.info("Calling Gemini model %s (url=%s)", model, url)

    try:
        resp = requests.post(url, json=payload, timeout=30)
    except Exception as e:
        logger.exception("HTTP request to Gemini failed: %s", e)
        raise RuntimeError(f"Failed to call Gemini API: {e}") from e

    # Always log full raw response for debugging (but don't leak in production logs)
    text = None
    try:
        raw = resp.text
        logger.debug("Gemini raw response status=%s body=%s", resp.status_code, raw)
        j = resp.json()
    except Exception:
        # Couldn't parse JSON; return raw text for downstream processing
        logger.warning("Gemini returned non-JSON response; using raw text")
        raw = resp.text
        return raw

    # Try several common response shapes
    # 1) {"candidates": [{"content": "..."}, ...]}
    candidates = j.get("candidates") if isinstance(j, dict) else None
    if candidates and isinstance(candidates, list) and len(candidates) > 0:
        first = candidates[0]
        # content might be a string under 'content' or 'output' or 'message'
        for key in ("content", "output", "message", "text"):
            if isinstance(first.get(key), str):
                return first.get(key)
        # sometimes content is nested
        first_str = json.dumps(first)
        return first_str

    # 2) {"output": "..."}
    if isinstance(j.get("output"), str):
        return j.get("output")

    # 3) Try 'candidates[0].content[0].text'
    try:
        return j["candidates"][0]["content"][0]["text"]
    except Exception:
        pass

    # Fallback: return full JSON string so caller can attempt to parse
    return json.dumps(j)


def _extract_json_from_text(text: str) -> str:
    """Attempt to extract the first JSON object or array from a free-text block.

    Simple heuristic: find first '{' and last '}', or first '[' and last ']'.
    """
    if not text or not isinstance(text, str):
        raise ValueError("No text to extract JSON from")

    # Try to find object
    obj_start = text.find("{")
    obj_end = text.rfind("}")
    arr_start = text.find("[")
    arr_end = text.rfind("]")

    # Prefer object if it appears to be well-formed
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        return text[obj_start:obj_end + 1]

    if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
        return text[arr_start:arr_end + 1]

    # If nothing found, raise
    raise ValueError("Could not extract JSON from LLM text")


def generate_summary(topic: str, max_length: int = 400) -> str:
    """Generate a short study summary using Gemini.

    Returns a string summary. Raises RuntimeError on failures.
    """
    prompt = (
        "Provide a concise study summary for the following topic."
        " Keep it factual and split into 2-4 short paragraphs."
        f" Topic: {topic}"
    )

    try:
        text = _call_gemini(prompt, temperature=0.2, max_output_tokens=max_length)
        # If the service returned a JSON blob, try to extract text content
        if isinstance(text, str):
            # if JSON-looking, try to parse
            try:
                parsed = json.loads(text)
                # If parsed contains top-level text, try to find it
                if isinstance(parsed, dict):
                    for k in ("output", "content", "text", "summary"):
                        if k in parsed and isinstance(parsed[k], str):
                            return parsed[k].strip()
                # fallback to joining serialized dict
                return json.dumps(parsed)
            except Exception:
                return text.strip()
        else:
            return str(text).strip()
    except Exception as e:
        logger.exception("Summary generation failed: %s", e)
        raise RuntimeError(f"Summary generation failed: {e}") from e


def generate_mcqs(topic: str, number_of_questions: int = 5, difficulty: str = "medium") -> List[Dict[str, Any]]:
    """Generate MCQs for a topic using Gemini.

    Returns a list of dicts: {question, options, answer} where answer is the
    index (0-3) of the correct option. Raises RuntimeError on failure.
    """

    # Normalize inputs
    number_of_questions = max(1, min(50, int(number_of_questions)))
    difficulty = (difficulty or "medium").lower()

    user_prompt = f"""
You are an exam-question generator. Create {number_of_questions} multiple-choice questions (MCQs)
about the following topic: {topic}

Requirements:
- Return ONLY valid JSON with an object containing a single key "mcqs" which is a list.
- Each MCQ must be an object with: "question" (string), "options" (array of 4 strings), and "answer" (integer index 0-3).
- Difficulty: {difficulty} (use simpler language for 'easy', more detail for 'hard').
- Avoid numbering or extra commentary outside the JSON.

Example:
{{
  "mcqs": [
    {{"question": "...", "options": ["A","B","C","D"], "answer": 2}},
    ...
  ]
}}
"""

    try:
        text = _call_gemini(user_prompt, temperature=0.3, max_output_tokens=800)

        logger.info("Raw Gemini reply length=%s", len(text) if isinstance(text, str) else 0)
        logger.debug("Raw Gemini reply repr=%s", repr(text))

        # If the text appears to be JSON or contains JSON, try to extract it
        def _attempt_parse(candidate_text: str):
            """Try to parse candidate_text as JSON. Returns parsed JSON or raises."""
            try:
                return json.loads(candidate_text)
            except Exception:
                # Try to extract JSON substring heuristically
                snippet = _extract_json_from_text(candidate_text)
                return json.loads(snippet)

        parsed_json = None
        try:
            parsed_json = _attempt_parse(text)
        except Exception as e_first:
            # First parse failed — try one corrective re-prompt asking the model to return strict JSON only.
            logger.warning("Initial JSON parse failed, attempting a repair re-prompt: %s", e_first)
            repair_prompt = (
                "The previous response was not valid JSON."
                " You must now RESPOND WITH VALID JSON ONLY, and nothing else."
                " The JSON must be an object with the single key \"mcqs\" whose value is an array of"
                " objects each having {\"question\": string, \"options\": [4 strings], \"answer\": int}.")
            # Provide the original raw reply as context to help the model correct itself.
            repair_context = f"Previous reply:\n{text}\n\n{repair_prompt}"
            try:
                repaired = _call_gemini(repair_context, temperature=0.0, max_output_tokens=600)
                logger.debug("Repair attempt raw reply=%s", repr(repaired))
                parsed_json = _attempt_parse(repaired)
            except Exception as e2:
                logger.warning("Repair attempt failed: %s", e2)
                # Surface the original failure and raw reply for debugging
                raise RuntimeError(f"Failed to parse JSON from Gemini reply. First error: {e_first}; repair error: {e2}\nRaw reply: {text}") from e2

        mcqs = parsed_json.get("mcqs") if isinstance(parsed_json, dict) else parsed_json

        if not isinstance(mcqs, list):
            raise RuntimeError("LLM returned JSON but 'mcqs' is not a list")

        normalized: List[Dict[str, Any]] = []
        for idx, item in enumerate(mcqs):
            if not isinstance(item, dict):
                logger.warning("Skipping non-dict MCQ item at index %s: %s", idx, item)
                continue
            q = item.get("question")
            opts = item.get("options")
            ans = item.get("answer")
            if q and isinstance(opts, list) and len(opts) == 4 and isinstance(ans, int):
                normalized.append({"question": q, "options": opts, "answer": ans})
            else:
                logger.warning("Skipping malformed MCQ at index %s: %s", idx, item)

        return normalized
    except Exception as e:
        logger.exception("Failed to generate MCQs: %s", e)
        raise RuntimeError(f"Failed to generate MCQs: {e}") from e

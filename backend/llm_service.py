import os
import json
import logging
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_gemini_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _call_gemini(prompt: str, temperature: float = 0.2, max_output_tokens: int = 1024) -> str:
    api_key = _get_gemini_key()

    if not api_key:
        raise RuntimeError("Missing Gemini API key. Set GEMINI_API_KEY in .env file.")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response_text = response.text

        try:
            data = response.json()
        except Exception:
            raise RuntimeError(f"Gemini returned non-JSON response: {response_text}")

        if response.status_code != 200:
            raise RuntimeError(f"Gemini API error {response.status_code}: {response_text}")

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            raise RuntimeError(f"Could not extract text from Gemini response: {response_text}")

    except Exception as e:
        logger.exception("Gemini API call failed")
        raise RuntimeError(f"Gemini API call failed: {e}") from e


def _extract_json_from_text(text: str) -> str:
    if not text:
        raise ValueError("No text to extract JSON from")

    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()
    elif text.startswith("```"):
        text = text.replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    raise ValueError("Could not extract JSON from Gemini response")


def generate_summary(topic: str, max_length: int = 400) -> str:
    prompt = f"""
Provide a concise study summary for the following topic.
Keep it factual and split into 2-4 short paragraphs.

Topic: {topic}
"""

    try:
        result = _call_gemini(prompt, temperature=0.2, max_output_tokens=max_length)
        return result.strip()
    except Exception as e:
        raise RuntimeError(f"Summary generation failed: {e}") from e


def generate_mcqs(topic: str, number_of_questions: int = 5, difficulty: str = "medium") -> List[Dict[str, Any]]:
    number_of_questions = max(1, min(20, int(number_of_questions)))
    difficulty = (difficulty or "medium").lower()

    prompt = f"""
Create {number_of_questions} multiple-choice questions about this topic:

Topic: {topic}

Return ONLY valid JSON. Do not use markdown. Do not explain.

Format:
{{
  "mcqs": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": 0
    }}
  ]
}}

Rules:
- Each question must have exactly 4 options.
- answer must be integer index from 0 to 3.
- Difficulty: {difficulty}
"""

    try:
        text = _call_gemini(prompt, temperature=0.3, max_output_tokens=1500)

        try:
            parsed = json.loads(text)
        except Exception:
            json_text = _extract_json_from_text(text)
            parsed = json.loads(json_text)

        mcqs = parsed.get("mcqs")

        if not isinstance(mcqs, list):
            raise RuntimeError("Gemini returned JSON but mcqs is not a list")

        final_mcqs = []

        for item in mcqs:
            question = item.get("question")
            options = item.get("options")
            answer = item.get("answer")

            if (
                isinstance(question, str)
                and isinstance(options, list)
                and len(options) == 4
                and isinstance(answer, int)
                and 0 <= answer <= 3
            ):
                final_mcqs.append({
                    "question": question,
                    "options": options,
                    "answer": answer
                })

        if not final_mcqs:
            raise RuntimeError("No valid MCQs generated")

        return final_mcqs

    except Exception as e:
        raise RuntimeError(f"MCQ generation failed: {e}") from e
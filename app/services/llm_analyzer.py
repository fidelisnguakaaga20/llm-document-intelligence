import json
import time
from typing import Tuple, Dict, Any

from openai import OpenAI
from app.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are a document analysis engine.
Return ONLY valid JSON with this schema:

{
  "summary": "3-5 sentences",
  "key_topics": ["topic1", "topic2", "..."],
  "sentiment": "positive|negative|neutral|mixed",
  "actionable_items": ["item1", "item2", "..."]
}

Rules:
- If no actionable items, return an empty list.
- key_topics must be a list of short phrases.
- sentiment must be one of the allowed strings.
- Do not include markdown. Do not include extra keys.
""".strip()


def analyze_text_once(text: str) -> Tuple[bool, Dict[str, Any] | str]:
    if not OPENAI_API_KEY:
        return False, "OPENAI_API_KEY is not set"

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Document text:\n\n{text[:20000]}"},
            ],
            temperature=0.2,
        )

        content = resp.choices[0].message.content.strip()

        # Must be JSON
        data = json.loads(content)

        # Basic schema checks
        if not isinstance(data.get("summary"), str):
            return False, "LLM output invalid: summary missing"
        if not isinstance(data.get("key_topics"), list):
            return False, "LLM output invalid: key_topics missing"
        if data.get("sentiment") not in {"positive", "negative", "neutral", "mixed"}:
            return False, "LLM output invalid: sentiment invalid"
        if not isinstance(data.get("actionable_items"), list):
            return False, "LLM output invalid: actionable_items missing"

        return True, data

    except Exception as e:
        return False, f"LLM error: {str(e)}"


def analyze_with_retry(text: str, retry_delay_sec: float = 0.8) -> Tuple[bool, Dict[str, Any] | str]:
    ok, result = analyze_text_once(text)
    if ok:
        return True, result

    # Retry once
    time.sleep(retry_delay_sec)
    ok2, result2 = analyze_text_once(text)
    if ok2:
        return True, result2

    return False, result2
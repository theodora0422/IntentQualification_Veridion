import json
import os
from google import genai

LLM_CANDIDATE_JUDGMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "enum": ["strong_match", "possible_match", "weak_match", "not_match"],
        },
        "llm_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10,
        },
        "explanation": {
            "type": "string",
        },
    },
    "required": ["label", "llm_score", "explanation"],
}

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=api_key)

def call_openai_llm_with_json_schema(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": LLM_CANDIDATE_JUDGMENT_SCHEMA,
                "temperature": 0,
            },
        )

        text = response.text.strip()
        print("[DEBUG] raw LLM response:", text)
        return text

    except Exception as e:
        print(f"[WARNING] Gemini API call failed: {e}")
        return json.dumps({
            "label": "possible_match",
            "llm_score": 0,
            "explanation": "LLM unavailable; keeping deterministic ranking."
        })
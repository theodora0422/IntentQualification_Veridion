import json
from openai import OpenAI


client = OpenAI()


def call_openai_llm(prompt: str):
    #real OpenAI API call using the Responses API.
    response = client.responses.create(
        model="gpt-5.4",
        input=prompt,
    )
    return response.output_text.strip()


def call_openai_llm_with_json_schema(prompt: str) -> str:

    response = client.responses.create(
        model="gpt-5.4",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "llm_candidate_judgment",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "label": {
                            "type": "string",
                            "enum": ["strong_match", "possible_match", "weak_match", "not_a_match"]
                        },
                        "llm_score": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 10
                        },
                        "explanation": {
                            "type": "string"
                        }
                    },
                    "required": ["label", "llm_score", "explanation"]
                }
            }
        }
    )

    return response.output_text.strip()
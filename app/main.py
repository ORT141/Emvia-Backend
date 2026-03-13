import hashlib
import json
import os

from fastapi import FastAPI, Request
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CACHE_DIR = "cache"

os.makedirs(CACHE_DIR, exist_ok=True)


class SurveyRequest(BaseModel):
    safe_color: str
    calming_pattern: str
    calming_item: str
    sound_trigger: str
    calming_action: str
    panic_style: str
    support_message: str


def cache_key(data):
    s = json.dumps(data, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()


def cache_path(key):
    return f"{CACHE_DIR}/{key}.json"


@app.post("/survey")
async def generate(data: SurveyRequest, request: Request):
    user_agent = request.headers.get("user-agent", "")

    if user_agent != "Emvia/1.0":
        return {"error": "not_found"}

    key = cache_key(data.model_dump())
    path = cache_path(key)

    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)

    prompt = f"""
SYSTEM INSTRUCTION: You are an assistant that MUST respond ONLY with valid JSON and nothing else. The JSON must exactly match the schema in 'Return JSON' below. Use Ukrainian for all `words`. 

Fields:
1) `pattern`: MUST be exactly one of the following English tokens (use this exact spelling):
   - moon, sun, cloud, star, tree, flower, triangle, rectangle, circle
2) `pattern_en`: matching token from above.
3) `stress_type`: MUST be exactly one of: battery, anchor, shield. Choose the one that best fits the user's "panic style" or "support message" contextually.
4) `words`: five calming Ukrainian words (array of 5 strings).
5) `color`: a hex color code that matches the chosen color or theme (string, e.g., "#A7E9D3").

Do NOT include explanations, backticks, or any additional text.

User survey results:

Safe color: {data.safe_color}
Pattern: {data.calming_pattern}
Item: {data.calming_item}
Sound trigger: {data.sound_trigger}
Calming action: {data.calming_action}
Panic style: {data.panic_style}
Support message: {data.support_message}

Return JSON (exact schema):
{{
 "words": ["word1", "word2", "word3", "word4", "word5"],
 "pattern": "string",
 "pattern_en": "string",
 "stress_type": "string",
 "color": "#HEXCODE"
}}
"""

    response = client.responses.create(model="gpt-4.1-mini", input=prompt)

    raw = response.output_text

    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {"error": "invalid_json", "raw": raw}

    with open(path, "w") as f:
        json.dump(parsed, f, ensure_ascii=False)

    return parsed

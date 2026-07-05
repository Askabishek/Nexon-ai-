from groq import Groq
from core.config import GROQ_API_KEY, GROQ_MODEL
import json

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are NEXORA's Career Agent — an expert career counselor for India.
You help with jobs, resume, internships, salary, skills, interview prep, career switching.

IMPORTANT: Respond ONLY in this JSON format, no markdown, no extra text:
{
  "recommendation": "main actionable advice here",
  "confidence": 0.85,
  "reason": "why this query is career-related",
  "risk": "risks or things to be careful about"
}

confidence must be between 0.0 and 1.0. Be India-specific and practical."""


def run(query: str, context: str = "") -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_content = f"Context:\n{context}\n\nQuery: {query}" if context else query
    messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()

        print(raw)
        parsed = json.loads(raw)
        return {
            "agent": "Career",
            "icon": "💼",
            "recommendation": parsed.get("recommendation", ""),
            "confidence": float(parsed.get("confidence", 0.75)),
            "reason": parsed.get("reason", ""),
            "risk": parsed.get("risk", ""),
            "status": "success",
        }
    except Exception as e:
        # added by vanshita
        import traceback

        print("=" * 60)
        print("CAREER AGENT ERROR")
        traceback.print_exc()
        print("=" * 60)
   ###
        return {
            "agent": "Career",
            "icon": "💼",
            "recommendation": f"Career Agent error: {str(e)}",
            "confidence": 0.0,
            "reason": "",
            "risk": "",
            "status": "error",
        }

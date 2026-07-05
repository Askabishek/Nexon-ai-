from groq import Groq
from core.config import GROQ_API_KEY, GROQ_MODEL, AGENT_METADATA, AGENT_CONFIDENCE_THRESHOLD
import json
#for DB added by vanshita
from core.decision_engine import synthesize

client = Groq(api_key=GROQ_API_KEY)


def detect_intent(user_query: str) -> dict:
    """
    Uses keyword scoring + LLM fallback to detect which agents to invoke.
    Returns: { agent_name: confidence_score (0.0 - 1.0) }
    """
    query_lower = user_query.lower()
    scores = {}

    for agent_key, meta in AGENT_METADATA.items():
        hits = sum(1 for kw in meta["keywords"] if kw in query_lower)
        scores[agent_key] = round(min(hits / 3, 1.0), 2)  # normalize to 0-1

    # If no keyword hits, fallback to LLM for intent classification
    if all(v == 0 for v in scores.values()):
        scores = _llm_intent_fallback(user_query)

    return scores


def _llm_intent_fallback(user_query: str) -> dict:
    """Ask Groq to classify intent when keywords miss."""
    system_prompt = """You are an intent classifier for NEXORA, an AI assistant.
Classify the user query into one or more of these agents:
- career: jobs, resume, interviews, salary, employment
- government: schemes, subsidies, documents, welfare, portals
- education: exams, colleges, courses, scholarships, admissions
- health: symptoms, hospitals, wellness, medical schemes

Respond ONLY with a valid JSON object like:
{"career": 0.8, "government": 0.1, "education": 0.0, "health": 0.0}
Scores must sum to 1.0. No explanation, no markdown."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            temperature=0.1,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception:
        # Safe fallback: equal distribution
        return {"career": 0.25, "government": 0.25, "education": 0.25, "health": 0.25}


def route_agents(intent_scores: dict) -> list[str]:
    """Return list of agent keys that pass the confidence threshold."""
    return [
        agent
        for agent, score in intent_scores.items()
        if score >= AGENT_CONFIDENCE_THRESHOLD
    ]

# mongoDB logging added by vanshita (stores conversation memory for future personalization)
def process_query(user_query):
    intent_scores = detect_intent(user_query)
    agents = route_agents(intent_scores)

    response = synthesize(user_query, agents, intent_scores)

    return response
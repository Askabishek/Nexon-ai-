from groq import Groq
from core.config import GROQ_API_KEY, GROQ_MODEL
from core.schema import AgentResponse, OrchestratorResponse, calculate_overall_confidence
from datetime import datetime

client = Groq(api_key=GROQ_API_KEY)


def synthesize(user_query: str, agent_results: list[dict], intent_scores: dict) -> OrchestratorResponse:
    """
    Merge all agent outputs → OrchestratorResponse (matches MongoDB schema exactly).
    """
    active_results = [r for r in agent_results if r["status"] == "success"]

    if not active_results:
        return OrchestratorResponse(
            query=user_query,
            agents_used=[],
            responses=[],
            final_response="⚠️ NEXORA could not process your request. Please rephrase.",
            overall_confidence=0.0,
        )

    # Build AgentResponse objects
    agent_responses = [
        AgentResponse(
            agent=r["agent"],
            recommendation=r["recommendation"],
            confidence=r["confidence"],
            reason=r["reason"],
            risk=r["risk"],
        )
        for r in active_results
    ]

    # Single agent — no synthesis needed
    if len(active_results) == 1:
        final = active_results[0]["recommendation"]
    else:
        final = _llm_synthesize(user_query, active_results)

    overall_conf = calculate_overall_confidence(agent_responses)

    return OrchestratorResponse(
        query=user_query,
        agents_used=[r["agent"] for r in active_results],
        responses=agent_responses,
        final_response=final,
        overall_confidence=overall_conf,
        timestamp=datetime.utcnow(),
    )


def _llm_synthesize(user_query: str, active_results: list[dict]) -> str:
    system_prompt = """You are NEXORA's Decision Engine. Synthesize insights from multiple agents into one unified, helpful response.
- No repetition across sections
- Connect related insights
- Use markdown with clear headings
- Add a brief Key Takeaway at the end
- Max 400 words. Sound like one assistant, not multiple agents."""

    agent_sections = "\n\n".join(
        f"### {r['agent']} Agent\nRecommendation: {r['recommendation']}\nReason: {r['reason']}\nRisk: {r['risk']}"
        for r in active_results
    )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {user_query}\n\n{agent_sections}"},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "\n\n".join(
            f"**{r['agent']}**: {r['recommendation']}" for r in active_results
        )


def get_active_agent_summary(intent_scores: dict, routed_agents: list[str]) -> list[dict]:
    from core.config import AGENT_METADATA
    summary = []
    for agent_key in routed_agents:
        meta = AGENT_METADATA[agent_key]
        summary.append({
            "key": agent_key,
            "name": meta["name"],
            "icon": meta["icon"],
            "confidence": intent_scores.get(agent_key, 0),
        })
    return sorted(summary, key=lambda x: x["confidence"], reverse=True)

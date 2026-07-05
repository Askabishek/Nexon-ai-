from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─────────────────────────────────────────────
# Agent Response Schema
# ─────────────────────────────────────────────
class AgentResponse(BaseModel):
    agent: str                          # "Education", "Career", etc.
    recommendation: str                 # Main recommendation text
    confidence: float                   # 0.0 - 1.0
    reason: str                         # Why this agent was relevant
    risk: str                           # Risks / things to watch out for


# ─────────────────────────────────────────────
# Orchestrator Response Schema
# ─────────────────────────────────────────────
class OrchestratorResponse(BaseModel):
    query: str
    agents_used: List[str]
    responses: List[AgentResponse]
    final_response: str
    overall_confidence: float           # avg of all agent confidences
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# Chat History Schema
# ─────────────────────────────────────────────
class ChatHistory(BaseModel):
    user_id: str                        # firebase_uid
    query: str
    response: OrchestratorResponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# User Schema
# ─────────────────────────────────────────────
class User(BaseModel):
    firebase_uid: str
    name: str
    email: str
    photo_url: Optional[str] = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# Preferences Schema
# ─────────────────────────────────────────────
class Preferences(BaseModel):
    user_id: str                        # firebase_uid
    language: str = "English"
    theme: str = "Light"


# ─────────────────────────────────────────────
# Helper — Calculate Overall Confidence
# ─────────────────────────────────────────────
def calculate_overall_confidence(responses: List[AgentResponse]) -> float:
    if not responses:
        return 0.0
    return round(sum(r.confidence for r in responses) / len(responses), 2)

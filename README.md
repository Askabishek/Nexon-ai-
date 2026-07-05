# 🧠 NEXORA — Multi-Agent AI Assistant

> Career · Education · Health · Government — one unified interface.

## Architecture

```
User Query (Text / PDF / Image)
        │
        ▼
  Streamlit Frontend
        │
        ▼
  🧠 Orchestrator (Intent Detection + Routing)
        │
   ┌────┴────┬────────┬────────┐
   ▼         ▼        ▼        ▼
💼 Career  📚 Edu  🩺 Health 🏛️ Govt
   └────┬────┴────────┴────────┘
        ▼
  ⚖️ Decision Engine (Synthesis via Groq)
        ▼
  📊 Final Structured Response
```

## Setup

```bash
git clone <repo>
cd nexora
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
streamlit run app.py
```

## File Structure

```
nexora/
├── app.py                   # Streamlit UI
├── requirements.txt
├── .env.example
├── core/
│   ├── config.py            # Constants, agent metadata
│   ├── orchestrator.py      # Intent detection + routing
│   └── decision_engine.py   # Synthesis + merging
├── agents/
│   ├── career_agent.py
│   ├── government_agent.py
│   ├── education_agent.py
│   └── health_agent.py
└── utils/
    └── multimodal.py        # PDF / image extraction
```

## Key Features

- **Parallel agent execution** via `concurrent.futures`
- **Keyword + LLM hybrid routing** — fast keyword match, LLM fallback
- **PDF/TXT context injection** into agent prompts
- **Decision Engine synthesis** — merges multi-agent outputs into one clean response
- **Query history** in sidebar
- **Dark glassmorphism UI** with gradient accents

## Agents

| Agent | Domain | Model |
|-------|---------|-------|
| 💼 Career | Jobs, Resume, Skills | Groq Llama3-70b |
| 🏛️ Government | Schemes, Documents | Groq Llama3-70b |
| 📚 Education | Exams, Scholarships | Groq Llama3-70b |
| 🩺 Health | Wellness, PM-JAY | Groq Llama3-70b |

## Roadmap (Phase 2)

- [ ] Voice input (Whisper API)
- [ ] Response caching (Redis / st.cache)
- [ ] Tamil/Hindi multilingual support
- [ ] State-specific scheme database
- [ ] User login + history persistence

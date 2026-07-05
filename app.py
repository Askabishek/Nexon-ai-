import datetime

from utils.cache import get_cached_response, save_response #added by vanshita
import streamlit as st
import concurrent.futures
import time
from database.mongodb import log_interaction

from core.orchestrator import detect_intent, route_agents
from core.decision_engine import synthesize, get_active_agent_summary
from utils.multimodal import get_file_context
from agents import career_agent, government_agent, education_agent, health_agent
from core.config import AGENT_METADATA

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="NEXORA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

AGENT_MAP = {
    "career": career_agent,
    "government": government_agent,
    "education": education_agent,
    "health": health_agent,
}


with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');

#     html, body, [class*="css"] {
#         font-family: 'Inter', sans-serif;
#     }

#     .stApp {
#         background: #0d0f14;
#         color: #e8eaf0;
#     }

#     /* Header */
#     .nexora-header {
#         text-align: center;
#         padding: 2rem 0 1rem;
#     }
#     .nexora-title {
#         font-family: 'Space Grotesk', sans-serif;
#         font-size: 3rem;
#         font-weight: 700;
#         background: linear-gradient(135deg, #7c6af7, #5eb8ff, #7c6af7);
#         background-size: 200% auto;
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         animation: shine 3s linear infinite;
#         letter-spacing: -1px;
#     }
#     @keyframes shine {
#         to { background-position: 200% center; }
#     }
#     .nexora-tagline {
#         font-size: 1rem;
#         color: #8890a8;
#         margin-top: 0.25rem;
#         font-weight: 400;
#     }

#     /* Agent pills */
#     .agent-pill {
#         display: inline-block;
#         background: #1a1d26;
#         border: 1px solid #2a2d3a;
#         border-radius: 20px;
#         padding: 4px 12px;
#         font-size: 0.78rem;
#         color: #8890a8;
#         margin: 2px;
#     }
#     .agent-pill.active {
#         background: #1e1a3a;
#         border-color: #7c6af7;
#         color: #b0a8ff;
#     }

#     /* Response card */
#     .response-card {
#         background: #13161f;
#         border: 1px solid #1e2130;
#         border-radius: 12px;
#         padding: 1.5rem;
#         margin: 1rem 0;
#     }

#     /* Agent result card */
#     .agent-card {
#         background: #0f1218;
#         border: 1px solid #1a1d26;
#         border-left: 3px solid #7c6af7;
#         border-radius: 8px;
#         padding: 1rem 1.25rem;
#         margin: 0.75rem 0;
#     }
#     .agent-card-header {
#         font-size: 0.85rem;
#         font-weight: 600;
#         color: #7c6af7;
#         margin-bottom: 0.5rem;
#     }

#     /* Confidence bar */
#     .conf-bar-bg {
#         background: #1a1d26;
#         border-radius: 4px;
#         height: 4px;
#         width: 100%;
#         margin-top: 4px;
#     }
#     .conf-bar-fill {
#         height: 4px;
#         border-radius: 4px;
#         background: linear-gradient(90deg, #7c6af7, #5eb8ff);
#     }

#     /* Input area */
#     .stTextArea textarea {
#         background: #13161f !important;
#         border: 1px solid #2a2d3a !important;
#         border-radius: 10px !important;
#         color: #e8eaf0 !important;
#         font-size: 0.95rem !important;
#     }

#     /* Buttons */
#     .stButton > button {
#         background: linear-gradient(135deg, #7c6af7, #5eb8ff) !important;
#         border: none !important;
#         border-radius: 8px !important;
#         color: white !important;
#         font-weight: 600 !important;
#         font-size: 0.95rem !important;
#         padding: 0.6rem 2rem !important;
#         width: 100% !important;
#     }
#     .stButton > button:hover {
#         opacity: 0.88 !important;
#         transform: translateY(-1px);
#     }

#     /* Sidebar */
#     [data-testid="stSidebar"] {
#         background: #0f1218 !important;
#         border-right: 1px solid #1a1d26;
#     }

#     /* Divider */
#     hr { border-color: #1a1d26 !important; }

#     /* Expander */
#     .streamlit-expanderHeader {
#         background: #13161f !important;
#         color: #8890a8 !important;
#     }

#     /* History item */
#     .history-item {
#         background: #13161f;
#         border: 1px solid #1a1d26;
#         border-radius: 8px;
#         padding: 0.75rem 1rem;
#         margin: 0.4rem 0;
#         cursor: pointer;
#         font-size: 0.85rem;
#         color: #8890a8;
#     }
# </style>
# """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None


# MongoDB tracking (ADDED BY VANSHITA)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(time.time())

if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user"  # will be replaced by Firebase later


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 NEXORA")
    st.markdown("<p style='color:#8890a8;font-size:0.82rem;'>Multi-Agent AI Assistant</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("**📎 Upload Document**")
    uploaded_file = st.file_uploader(
        "PDF, TXT, or Image",
        type=["pdf", "txt", "png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name}")

    st.divider()

    st.markdown("**🤖 Available Agents**")
    for key, meta in AGENT_METADATA.items():
        st.markdown(
            f"<div class='agent-pill'>{meta['icon']} {meta['name']}</div>",
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown("**📜 Query History**")
    if not st.session_state.history:
        st.markdown("<p style='color:#555;font-size:0.8rem;'>No queries yet.</p>", unsafe_allow_html=True)
    else:
        for i, h in enumerate(reversed(st.session_state.history[-6:])):
            truncated = h["query"][:45] + "..." if len(h["query"]) > 45 else h["query"]
            agents_used = " ".join([AGENT_METADATA[a]["icon"] for a in h["agents"]])
            st.markdown(
                f"<div class='history-item'>{agents_used} {truncated}</div>",
                unsafe_allow_html=True
            )

    st.divider()
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.last_result = None
        st.rerun()


# ─────────────────────────────────────────────
# Main Area
# ─────────────────────────────────────────────
st.markdown("""
<div class='nexora-header'>
    <div class='nexora-title'>NEXORA</div>
    <div class='nexora-tagline'>Multi-Agent AI · Career · Education · Health · Government</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Query Input
col1, col2 = st.columns([5, 1])
with col1:
    user_query = st.text_area(
        "Ask NEXORA anything...",
        placeholder="e.g. I'm a fresher from a tier-3 college. How do I get an internship and are there any government skill programs?",
        height=100,
        label_visibility="collapsed",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.button("⚡ Ask")


# ─────────────────────────────────────────────
# Processing
# ─────────────────────────────────────────────
if submit and user_query.strip():
    with st.spinner(""):
        # Step 1: Extract file context
        file_context = get_file_context(uploaded_file) if uploaded_file else ""

        # Check if this query is already cached
        cached_response = get_cached_response(user_query, file_context)

        # Check if this query is already cached => added by vanshita
        if cached_response is not None:
            st.info("⚡ Loaded from Cache")
            st.session_state.last_result = cached_response
            st.rerun() 

        else:

            # Step 2: Intent detection
            intent_scores = detect_intent(user_query)
            routed_agent_keys = route_agents(intent_scores)

            if not routed_agent_keys:
                routed_agent_keys = ["career"]  # safe fallback

            # Step 3: Show routing info
            agent_summary = get_active_agent_summary(intent_scores, routed_agent_keys)

            routing_html = "<div style='margin:0.5rem 0;'><span style='color:#555;font-size:0.8rem;'>Routing to → </span>"
            for agent in agent_summary:
                conf_pct = int(agent["confidence"] * 100)
                routing_html += f"<span class='agent-pill active'>{agent['icon']} {agent['name']} {conf_pct}%</span>"
            routing_html += "</div>"
            st.markdown(routing_html, unsafe_allow_html=True)

            # Step 4: Run agents in parallel
            start_time = time.time()
            agent_results = []

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(AGENT_MAP[key].run, user_query, file_context): key
                    for key in routed_agent_keys
                }
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    print("AGENT RESULT:", result)
                    agent_results.append(result)

            elapsed = round(time.time() - start_time, 2)

            # Step 5: Decision Engine synthesis
            final_response = synthesize(user_query, agent_results, intent_scores)
            final_text = final_response.final_response

            # Log interaction to MongoDB => Added by vanshita
            response_data = {
                "summary": final_text,
                "agents": [
                    agent.model_dump(mode="json")
                    for agent in final_response.responses
                ]
            }

            log_interaction(
                user_id=st.session_state.user_id,
                query=user_query,
                response=response_data
            )


            # Save to history
            st.session_state.history.append({
                "query": user_query,
                "agents": routed_agent_keys,
                "response": final_text,
            })
            st.session_state.last_result = {
                "query": user_query,
                "agent_results": agent_results,
                "final_response": final_text,
                "elapsed": elapsed,
                "routed": routed_agent_keys,
            }

            # Save response in cache => added by vanshita
            save_response(
                user_query,
                file_context,
                st.session_state.last_result
            )

# ─────────────────────────────────────────────
# Display Results
# ─────────────────────────────────────────────
if st.session_state.last_result:
    result = st.session_state.last_result

    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:center;margin:1rem 0 0.5rem;'>
        <span style='font-family:Space Grotesk;font-weight:600;font-size:1.1rem;color:#e8eaf0;'>
            ⚡ NEXORA Response
        </span>
        <span style='color:#555;font-size:0.78rem;'>
            {result['elapsed']}s · {len(result['routed'])} agent(s)
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Final synthesized response
    st.markdown(f"<div class='response-card'>{result['final_response']}</div>", unsafe_allow_html=True)

    # Individual agent outputs (collapsible)
    if len(result["agent_results"]) > 1:
        with st.expander("🔍 View Individual Agent Outputs", expanded=False):
            for r in result["agent_results"]:
                st.markdown(f"""
                <div class='agent-card'>
                    <div class='agent-card-header'>{r['icon']} {r['name']}</div>
                    <div style='font-size:0.88rem;color:#c0c4d0;'>{r['response']}</div>
                </div>
                """, unsafe_allow_html=True)

elif not submit:
    # Welcome state
    st.markdown("""
    <div style='text-align:center;padding:1rem 1rem;color:#3a3f52;'>
        <div style='font-size:3rem;'>🧠</div>
        <div style='font-size:1.1rem;margin-top:0.2rem;'>Ask me anything across Career, Education, Health & Government</div>
        <div style='font-size:0.85rem;margin-top:0.2rem;'>Upload a PDF or image for context-aware answers</div>
    </div>
    """, unsafe_allow_html=True)

    # Sample queries
    st.markdown("**Try these:**")
    cols = st.columns(2)
    samples = [
        "How do I apply for Mudra loan as a small business owner?",
        "Best career path for a CSE fresher in 2025?",
        "What scholarships exist for OBC students in Tamil Nadu?",
        "How does Ayushman Bharat work and am I eligible?",
    ]
    for i, sample in enumerate(samples):
        with cols[i % 2]:
            if st.button(sample, key=f"sample_{i}"):
                st.session_state["prefill"] = sample
                st.rerun()

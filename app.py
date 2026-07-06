import datetime
import concurrent.futures
import time
import streamlit as st

from utils.cache import get_cached_response, save_response  # added by vanshita
try:
    from database.mongodb import log_interaction
except Exception:
    def log_interaction(*args, **kwargs):
        pass

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

# Read styles.css safely if it exists
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

AGENT_MAP = {
    "career": career_agent,
    "government": government_agent,
    "education": education_agent,
    "health": health_agent,
}

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
        file_context = get_file_context(uploaded_file) if uploaded_file else ""

        # Check if this query is already cached
        cached_response = get_cached_response(user_query, file_context)

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
                    agent_results.append(result)

            elapsed = round(time.time() - start_time, 2)

            # Step 5: Decision Engine synthesis (Returns OrchestratorResponse Object)
            final_response = synthesize(user_query, agent_results, intent_scores)

            # Log interaction to MongoDB
            response_data = {
                "summary": final_response.final_response,
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
                "response": final_response.final_response,
            })
            
            # Store everything as a safe serialized dict to unify cache and live processing formats
            st.session_state.last_result = {
                "query": user_query,
                "agent_results": agent_results,
                "final_response": final_response.final_response,
                "elapsed": elapsed,
                "routed": routed_agent_keys,
            }

            # Save response in cache
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
    
    # Extract data cleanly from uniform dict structures
    final_text = result.get("final_response", "")
    elapsed_time = result.get("elapsed", 0.0)
    
    st.markdown("### 🤖 Synthesized Insights")
    st.markdown(f"<p style='color:#8890a8; font-size:0.85rem;'>Response synthesized in {elapsed_time}s</p>", unsafe_allow_html=True)
    
    # Render final response inside your custom CSS card container
    st.markdown(f"""
    <div class="response-card">
        {final_text}
    </div>
    """, unsafe_allow_html=True)
    
    # Optional Breakdown Expander
    with st.expander("🔍 See Agent Breakdown"):
        for res in result.get("agent_results", []):
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-card-header">🧬 {res.get('agent', 'Unknown Agent').upper()} AGENT (Confidence: {int(res.get('confidence', 0)*100)}%)</div>
                <strong>Recommendation:</strong> {res.get('recommendation', '')}<br>
                <strong>Reasoning:</strong> {res.get('reason', '')}<br>
                <span style='color:#ff6b6b;'><strong>Risk Assessment:</strong> {res.get('risk', 'None')}</span>
            </div>
            """, unsafe_allow_html=True)

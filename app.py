"""
app.py — Streamlit interface for the Research and Eval Agent.

Replaces the terminal flow in main.py with a readable, interactive UI.
Auto-saves to state/sessions.json after every step.
Displays token usage and estimated cost for each research run.
"""

import json
import uuid
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

load_dotenv("config/.env")

from src.agent import run_research_agent  # noqa: E402  (must load .env first)
from src.schema import ResearchSession, UsageMetrics  # noqa: E402

STATE_PATH = "state/sessions.json"

st.set_page_config(page_title="Research and Eval Agent", layout="centered")


def save_session(session: ResearchSession) -> None:
    """Append or update this session in state/sessions.json."""
    try:
        with open(STATE_PATH, "r") as f:
            sessions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        sessions = []

    sessions = [s for s in sessions if s.get("session_id") != session["session_id"]]
    sessions.append(session)

    with open(STATE_PATH, "w") as f:
        json.dump(sessions, f, indent=2)


# --- Session state setup --------------------------------------------------

if "session" not in st.session_state:
    st.session_state.session = None
    st.session_state.stage = "topic_input"  # topic_input -> researching -> done
    st.session_state.usage = None  # holds token/cost info for the last run

# --- UI: Title -------------------------------------------------------------

st.title("Research and Eval Agent")
st.caption("Research a topic, then practice applying it through real scenarios.")

# --- Stage 1: Topic input ---------------------------------------------------

if st.session_state.stage == "topic_input":
    topic = st.text_input("What would you like to research?")

    if st.button("Research", type="primary") and topic:
        st.session_state.session = ResearchSession(
            session_id=str(uuid.uuid4()),
            topic=topic,
            messages=[],
            report=None,
            created_at=datetime.now(timezone.utc).isoformat(),
            usage=None,
        )
        st.session_state.stage = "researching"
        st.rerun()

# --- Stage 2: Run research --------------------------------------------------

elif st.session_state.stage == "researching":
    with st.spinner("Researching... this may take a minute."):
        result = run_research_agent(st.session_state.session["topic"])

    st.session_state.session["report"] = result["report"]
    st.session_state.usage = UsageMetrics(
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        cached_tokens=result["cached_tokens"],
        cost_usd=result["cost_usd"],
    )
    st.session_state.session["usage"] = st.session_state.usage
    save_session(st.session_state.session)
    st.session_state.stage = "done"
    st.rerun()

# --- Stage 3: Show the report -----------------------------------------------

elif st.session_state.stage == "done":
    st.markdown(st.session_state.session["report"])

    usage = st.session_state.usage
    if usage:
        col1, col2, col3 = st.columns(3)
        col1.metric("Input tokens", f"{usage['input_tokens']:,}")
        col2.metric("Output tokens", f"{usage['output_tokens']:,}")
        col3.metric("Est. cost", f"${usage['cost_usd']:.4f}")
        if usage["cached_tokens"]:
            st.caption(f"{usage['cached_tokens']:,} input tokens served from cache (90% cheaper)")

    st.divider()
    if st.button("Start a new topic"):
        st.session_state.session = None
        st.session_state.stage = "topic_input"
        st.session_state.usage = None
        st.rerun()

# --- Sidebar: past sessions --------------------------------------------------

with st.sidebar:
    st.subheader("Past sessions")
    try:
        with open(STATE_PATH, "r") as f:
            past = json.load(f)
        for s in reversed(past[-10:]):
            with st.expander(s.get("topic", "Untitled")):
                st.caption(s.get("created_at", ""))
                col_load, col_delete = st.columns(2)
                with col_load:
                    if st.button("Load", key=f"load_{s['session_id']}"):
                        st.session_state.session = s
                        st.session_state.usage = s.get("usage")
                        st.session_state.stage = "done"
                        st.rerun()
                with col_delete:
                    if st.button("Delete", key=f"delete_{s['session_id']}"):
                        remaining = [x for x in past if x.get("session_id") != s["session_id"]]
                        with open(STATE_PATH, "w") as f:
                            json.dump(remaining, f, indent=2)
                        current = st.session_state.session
                        if current and current.get("session_id") == s["session_id"]:
                            st.session_state.session = None
                            st.session_state.stage = "topic_input"
                            st.session_state.usage = None
                        st.rerun()
    except (FileNotFoundError, json.JSONDecodeError):
        st.caption("No past sessions yet.")
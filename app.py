"""
app.py — Research & Eval Agent, 5-page prototype.

Stages: topic_input → researching → research_done → context_input
        → generating → practice → evaluating → evaluation
"""

import json
import re
import uuid
from datetime import date, datetime, timezone

import streamlit as st
from dotenv import load_dotenv

load_dotenv("config/.env")

from src.agent import generate_scenarios, run_research_agent, run_structured_eval  # noqa: E402

STATE_PATH = "state/sessions.json"

st.set_page_config(
    page_title="Research & Eval Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main { background: #0F0F0F; }
[data-testid="stAppViewContainer"] { background: #0F0F0F; }
[data-testid="stMainBlockContainer"] { background: #0F0F0F; }
section[data-testid="stMain"] { background: #0F0F0F; }
[data-testid="stSidebar"] { background: #111111; border-right: 1px solid #222222; }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
[data-testid="stHeader"] { display: none !important; }
.block-container { padding-top: 1.5rem !important; padding-left: 3rem !important; padding-right: 3rem !important; }

/* Header banner */
.app-title { font-size: 16px; font-weight: 800; color: #FFFFFF; white-space: nowrap; margin: 0; padding: 0; }

/* Header card — multiple selectors cover Streamlit DOM variants across versions */
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="stHorizontalBlock"],
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div.stHorizontalBlock,
.element-container:has(.hdr-nav) + .element-container [data-testid="stHorizontalBlock"],
.element-container:has(.hdr-nav) + div [data-testid="stHorizontalBlock"],
.element-container:has(.hdr-nav) + [data-testid="stHorizontalBlock"] {
    background: #1A1A1A;
    border: 1.5px solid #F5C542;
    border-radius: 14px;
    padding: 20px 28px;
    margin-bottom: 32px;
    box-shadow: 0 2px 8px rgba(245,197,66,0.08);
    align-items: center;
    min-height: 68px;
}

/* Vertically center column contents */
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="column"],
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="column"] > div,
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="column"] > div > div,
.element-container:has(.hdr-nav) + div [data-testid="column"],
.element-container:has(.hdr-nav) + div [data-testid="column"] > div,
.element-container:has(.hdr-nav) + div [data-testid="column"] > div > div {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
}

/* Done-step buttons */
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="stButton"] button,
.element-container:has(.hdr-nav) + div [data-testid="stButton"] button {
    background: none !important; border: none !important; box-shadow: none !important;
    color: #999 !important; font-size: 13px !important; font-weight: 500 !important;
    padding: 0 !important; cursor: pointer !important; white-space: nowrap !important;
    display: flex !important; align-items: center !important; gap: 7px !important;
}
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="stButton"] button::before,
.element-container:has(.hdr-nav) + div [data-testid="stButton"] button::before {
    content: "✓";
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; min-width: 26px;
    background: #333333; color: #999;
    border-radius: 50%; font-size: 11px; font-weight: 800; flex-shrink: 0;
}
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="stButton"] button:hover,
.element-container:has(.hdr-nav) + div [data-testid="stButton"] button:hover { color: #FFFFFF !important; }
div:has([data-testid="stMarkdownContainer"] .hdr-nav) + div [data-testid="stButton"] button:hover::before,
.element-container:has(.hdr-nav) + div [data-testid="stButton"] button:hover::before { background: #555555; }

/* Cards */
.card {
    background: #1A1A1A; border-radius: 14px; padding: 24px;
    border: 1px solid #2A2A2A; margin-bottom: 20px;
}

/* Concept pills */
.concept-pill {
    display: inline-block; background: #2A2A2A; color: #F5C542;
    border-radius: 20px; padding: 4px 14px; font-size: 13px;
    margin: 3px; font-weight: 500;
}

/* Source list */
.source-item { padding: 10px 0; border-bottom: 1px solid #2A2A2A; }
.source-item:last-child { border-bottom: none; }
.source-num { font-weight: 700; color: #777; margin-right: 10px; font-size: 14px; }
.source-title { font-weight: 700; color: #FFFFFF; font-size: 14px; }
.source-sub { font-size: 13px; color: #666; padding-left: 34px; display: block; }

/* Scenario card */
.scenario-card {
    background: #1E1E1E; border-radius: 14px; padding: 22px; margin-bottom: 20px;
    border: 1px solid #2A2A2A;
}
.scenario-card h3 { margin: 0 0 10px; font-size: 18px; font-weight: 700; color: #FFFFFF; }
.scenario-card p  { margin: 0; color: #CCCCCC; line-height: 1.65; }

/* Tailored badge */
.tailored-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #2A2A2A; color: #F5C542; border-radius: 20px;
    padding: 5px 14px; font-size: 13px; font-weight: 500;
}

/* Score row */
.score-row { display: flex; gap: 12px; margin-bottom: 20px; }
.score-card { flex: 1; background: #1E1E1E; border-radius: 14px; padding: 18px 20px; border: 1px solid #2A2A2A; }
.score-value { font-size: 30px; font-weight: 800; color: #FFFFFF; margin-bottom: 4px; }
.score-label { font-size: 13px; color: #777; }

/* Typography helpers */
.section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
    color: #F5C542; margin-bottom: 4px;
}
.page-title   { font-size: 34px; font-weight: 800; color: #FFFFFF; margin-bottom: 8px; line-height: 1.2; }
.page-subtitle{ font-size: 15px; color: #777; margin-bottom: 28px; }

/* Sidebar session expanders */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: #1A1A1A; border-radius: 10px; border: 1px solid #2A2A2A;
    margin-bottom: 6px;
}
[data-testid="stSidebar"] details > summary span { font-weight: 700; color: #F5C542 !important; }

/* Saved label */
.saved-label { color: #F5C542; font-size: 13px; font-weight: 500; text-align: right; padding-top: 4px; }

/* Primary button — yellow/gold */
[data-testid="stButton"] button[kind="primary"] {
    background: #F5C542 !important;
    color: #0F0F0F !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}
[data-testid="stButton"] button[kind="primary"]:hover { background: #E6B530 !important; }

/* Secondary / suggestion pills — dark style */
[data-testid="stButton"] button[kind="secondary"] {
    background: #2A2A2A !important;
    color: #FFFFFF !important;
    border: 1px solid #3A3A3A !important;
    border-radius: 999px !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #333333 !important;
    border-color: #F5C542 !important;
}

/* Global text on dark bg */
.stMarkdown p, .stMarkdown li, .stText, label, .stCaption { color: #CCCCCC !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] label { color: #CCCCCC !important; }
strong { color: #FFFFFF !important; }

/* Markdown headings */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
.stMarkdown h4, .stMarkdown h5, .stMarkdown h6 { color: #FFFFFF !important; }

/* Markdown tables */
.stMarkdown table { border-collapse: collapse; width: 100%; }
.stMarkdown table th {
    color: #F5C542 !important;
    background: #1A1A1A !important;
    border-bottom: 1px solid #2A2A2A !important;
    font-size: 12px; letter-spacing: 0.05em; font-weight: 700;
    padding: 8px 12px;
}
.stMarkdown table td {
    color: #CCCCCC !important;
    background: transparent !important;
    border-bottom: 1px solid #222222 !important;
    padding: 8px 12px;
}
.stMarkdown table tr:hover td { background: #1A1A1A !important; }

/* Sidebar expander — open and closed states */
[data-testid="stSidebar"] [data-testid="stExpander"],
[data-testid="stSidebar"] [data-testid="stExpander"] details,
[data-testid="stSidebar"] details,
[data-testid="stSidebar"] details[open],
[data-testid="stSidebar"] details > div { background: #1A1A1A !important; color: #CCCCCC !important; }

/* Input fields */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #1E1E1E !important;
    color: #FFFFFF !important;
    border: 1px solid #333333 !important;
    border-radius: 8px !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder { color: #555555 !important; }
</style>
""", unsafe_allow_html=True)


# ─── Persistence helpers ───────────────────────────────────────────────────────

def save_session(session: dict) -> None:
    try:
        with open(STATE_PATH) as f:
            sessions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        sessions = []
    sessions = [s for s in sessions if s.get("session_id") != session["session_id"]]
    sessions.append(session)
    with open(STATE_PATH, "w") as f:
        json.dump(sessions, f, indent=2)


def load_sessions() -> list:
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ─── Report parsing ────────────────────────────────────────────────────────────

def parse_research_output(report: str) -> dict:
    """Extract RESEARCH_JSON metadata and SCENARIOS from the agent's report."""
    result: dict = {"summary": None, "key_concepts": [], "sources": [], "body": report, "scenarios": []}

    json_match = re.search(r"<RESEARCH_JSON>(.*?)</RESEARCH_JSON>", report, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1).strip())
            result["summary"] = data.get("summary")
            result["key_concepts"] = data.get("key_concepts", [])
            result["sources"] = data.get("sources", [])
        except json.JSONDecodeError:
            pass

    scenarios_match = re.search(r"<SCENARIOS>(.*?)</SCENARIOS>", report, re.DOTALL)
    if scenarios_match:
        try:
            result["scenarios"] = [{**s, "tailored": False} for s in json.loads(scenarios_match.group(1).strip())]
        except json.JSONDecodeError:
            pass

    if json_match and scenarios_match:
        result["body"] = report[json_match.end():scenarios_match.start()].strip()
    elif json_match:
        result["body"] = report[json_match.end():].strip()

    # Strip any inline scenario/task sections the agent may have added to the body.
    # Covers: "## The Scenario: ...", "## Practice Scenario", "## Your Task", "## Scenario 1"
    result["body"] = re.sub(
        r"(?im)^#{1,3}\s*(the scenario|practice scenario|your task|scenario[\s:]|\d+\.\s*scenario).*$(\n.*)*?(?=\n#{1,3}|\Z)",
        "",
        result["body"],
    ).strip()
    result["body"] = re.sub(
        r"(?i)after you respond.*?(scenario \d|evaluation).*?\n?",
        "",
        result["body"],
    ).strip()
    # If a "Scenario" section still leaks in as bold/unmarked text, cut everything from that point
    scenario_cutoff = re.search(r"(?im)^\*\*?(the scenario|scenario \d|practice scenario)", result["body"])
    if scenario_cutoff:
        result["body"] = result["body"][:scenario_cutoff.start()].strip()

    return result


# ─── UI helpers ───────────────────────────────────────────────────────────────

def _md_to_html(text: str) -> str:
    """Convert markdown bold/italic and escape $ for safe embedding inside HTML."""
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # Wrap $ in <code> — KaTeX auto-render skips ignoredTags (code, pre, script…),
    # so the dollar sign inside <code> never forms a $…$ delimiter pair.
    text = text.replace('$', '<code style="font-family:inherit;background:transparent;padding:0;color:inherit;">$</code>')
    text = text.replace('\n\n', '</p><p style="margin:8px 0;line-height:1.65;">')
    text = text.replace('\n', '<br>')
    return text


# Step 1=Research, 2=Learn, 3=Context, 4=Evaluation
STAGE_STEP = {
    "topic_input": 1, "researching": 1,
    "research_done": 2,
    "context_input": 3, "generating": 3, "practice": 3, "evaluating": 3,
    "evaluation": 4,
}



def _go_to_step(step_num: int) -> None:
    if step_num == 1:
        _reset_state()
    elif step_num == 2 and st.session_state.get("parsed_data"):
        st.session_state.stage = "research_done"
    elif step_num == 3 and st.session_state.get("parsed_data"):
        st.session_state.stage = "context_input"


def render_header() -> None:
    active = STAGE_STEP.get(st.session_state.stage, 1)
    steps = [("Research", 1), ("Learn", 2), ("Context", 3), ("Evaluation", 4)]

    st.markdown('<div class="hdr-nav"></div>', unsafe_allow_html=True)

    title_col, s1, c1, s2, c2, s3, c3, s4 = st.columns([2, 1.5, 0.2, 1.5, 0.2, 1.5, 0.2, 1.8])

    with title_col:
        st.markdown('<p class="app-title">Research &amp; Eval Agent</p>', unsafe_allow_html=True)

    for col, (label, step_num) in zip([s1, s2, s3, s4], steps):
        with col:
            if step_num < active:
                if st.button(label, key=f"step_nav_{step_num}"):
                    _go_to_step(step_num)
                    st.rerun()
            elif step_num == active:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:7px;">'
                    f'<div style="width:26px;height:26px;border-radius:50%;background:#F5C542;'
                    f'color:#0F0F0F;display:flex;align-items:center;justify-content:center;'
                    f'font-size:12px;font-weight:700;flex-shrink:0;">{step_num}</div>'
                    f'<span style="font-size:13px;font-weight:600;color:#FFFFFF;white-space:nowrap;">{label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:7px;">'
                    f'<div style="width:26px;height:26px;border-radius:50%;background:#2A2A2A;'
                    f'color:#555;display:flex;align-items:center;justify-content:center;'
                    f'font-size:12px;font-weight:700;flex-shrink:0;">{step_num}</div>'
                    f'<span style="font-size:13px;color:#555;white-space:nowrap;">{label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    for conn_col in [c1, c2, c3]:
        with conn_col:
            st.markdown('<div style="height:1px;background:#2A2A2A;"></div>', unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#555;margin-bottom:12px;">PAST SESSIONS</p>',
            unsafe_allow_html=True,
        )
        sessions = load_sessions()
        if not sessions:
            st.caption("No past sessions yet.")
            return

        for s in reversed(sessions[-10:]):
            topic = s.get("topic", "Untitled")
            done = len(s.get("scenario_results") or [])
            total = len(s.get("scenarios") or []) or 3
            created = s.get("created_at", "")[:10]
            today = date.today().isoformat()
            when = "today" if created == today else created
            meta = f"Studied {when} · {done}/{total} scenarios"

            with st.expander(topic):
                st.caption(meta)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Load", key=f"load_{s['session_id']}", use_container_width=True):
                        _load_session(s)
                        st.rerun()
                with c2:
                    if st.button("Delete", key=f"del_{s['session_id']}", use_container_width=True):
                        _delete_session(s["session_id"])
                        st.rerun()


# ─── State management ─────────────────────────────────────────────────────────

def _reset_state() -> None:
    for key, val in [
        ("stage", "topic_input"), ("session", None), ("parsed_data", None),
        ("scenarios", None), ("scenario_idx", 0), ("scenario_results", []),
        ("current_eval", None), ("current_response", ""), ("usage", None),
        ("user_context", ""),
    ]:
        st.session_state[key] = val


def _load_session(s: dict) -> None:
    st.session_state.session = s
    st.session_state.parsed_data = parse_research_output(s.get("report") or "")
    st.session_state.scenarios = s.get("scenarios") or st.session_state.parsed_data.get("scenarios", [])
    st.session_state.scenario_results = list(s.get("scenario_results") or [])
    st.session_state.scenario_idx = len(st.session_state.scenario_results)
    st.session_state.current_eval = None
    st.session_state.current_response = ""
    st.session_state.usage = s.get("usage")
    st.session_state.user_context = s.get("user_context", "")
    st.session_state.stage = "research_done"


def _delete_session(session_id: str) -> None:
    remaining = [s for s in load_sessions() if s.get("session_id") != session_id]
    with open(STATE_PATH, "w") as f:
        json.dump(remaining, f, indent=2)
    current = st.session_state.get("session")
    if current and current.get("session_id") == session_id:
        _reset_state()


if "stage" not in st.session_state:
    _reset_state()

# ─── Always render sidebar ─────────────────────────────────────────────────────

render_sidebar()

# ─── Page routing ─────────────────────────────────────────────────────────────

stage = st.session_state.stage

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Topic input
# ══════════════════════════════════════════════════════════════════════════════

if stage == "topic_input":
    render_header()

    st.markdown('<div class="page-title">What would you like to learn today?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Research any topic, then practice applying it through real-world scenarios.</div>',
        unsafe_allow_html=True,
    )

    # Apply a pill selection from the previous run before the widget is instantiated
    if "_topic_pending" in st.session_state:
        st.session_state.topic_field = st.session_state.pop("_topic_pending")

    st.markdown("**Topic**")
    st.text_input(
        "topic",
        key="topic_field",
        label_visibility="collapsed",
        placeholder="e.g. Game theory, supply & demand, cognitive biases...",
    )

    # Quick-select pills from past sessions
    sessions = load_sessions()
    if sessions:
        recent = [s.get("topic", "") for s in sessions[-4:] if s.get("topic")]
        if recent:
            cols = st.columns(len(recent))
            for i, t in enumerate(recent):
                with cols[i]:
                    if st.button(t, key=f"pill_{i}"):
                        st.session_state._topic_pending = t
                        st.rerun()

    st.markdown("")
    if st.button("Start research →", type="primary"):
        topic_val = st.session_state.get("topic_field", "").strip()
        if topic_val:
            st.session_state.session = {
                "session_id": str(uuid.uuid4()),
                "topic": topic_val,
                "messages": [],
                "report": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "usage": None,
                "scenarios": None,
                "scenario_results": [],
                "user_context": "",
            }
            st.session_state.stage = "researching"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# LOADING — Researching
# ══════════════════════════════════════════════════════════════════════════════

elif stage == "researching":
    render_header()
    topic = st.session_state.session["topic"]
    with st.spinner(f"Researching **{topic}**… this may take a minute."):
        result = run_research_agent(topic)

    st.session_state.session["report"] = result["report"]
    st.session_state.usage = {
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "cached_tokens": result["cached_tokens"],
        "cost_usd": result["cost_usd"],
    }
    st.session_state.session["usage"] = st.session_state.usage
    parsed = parse_research_output(result["report"])
    st.session_state.parsed_data = parsed
    st.session_state.scenarios = parsed.get("scenarios", [])
    st.session_state.session["scenarios"] = st.session_state.scenarios
    save_session(st.session_state.session)
    st.session_state.stage = "research_done"
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Research results (Learn)
# ══════════════════════════════════════════════════════════════════════════════

elif stage == "research_done":
    render_header()

    parsed = st.session_state.parsed_data or {}
    topic = st.session_state.session["topic"]
    summary = parsed.get("summary")
    key_concepts: list = parsed.get("key_concepts", [])
    sources: list = parsed.get("sources", [])

    st.markdown(f'<div class="page-title" style="font-size:30px;">{topic}</div>', unsafe_allow_html=True)

    if summary or key_concepts or sources:
        concepts_html = (
            '<div style="margin-top:16px;">'
            '<div style="font-weight:700;font-size:14px;margin-bottom:8px;">Key concepts</div>'
            + "".join(f'<span class="concept-pill">{c}</span>' for c in key_concepts)
            + '</div>'
        ) if key_concepts else ""

        sources_html = ""
        if sources:
            items = "".join(
                f'<div class="source-item">'
                f'<span class="source-num">{i:02d}</span>'
                f'<span class="source-title">{s.get("title", "")}</span>'
                f'<span class="source-sub">{s.get("subtitle", "")}</span>'
                f'</div>'
                for i, s in enumerate(sources, 1)
            )
            sources_html = f'<div style="margin-top:20px;">{items}</div>'

        st.markdown(
            f'<div class="card">'
            f'<p style="color:#333;line-height:1.7;margin:0;">{summary or ""}</p>'
            f'{concepts_html}'
            f'{sources_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        # Old session without structured output — show raw body
        body = parsed.get("body") or st.session_state.session.get("report", "")
        with st.container():
            st.markdown(body)

    if st.button("Practice with scenarios →", type="primary"):
        st.session_state.stage = "context_input"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Context input
# ══════════════════════════════════════════════════════════════════════════════

elif stage == "context_input":
    render_header()

    st.markdown('<div class="section-label">CONTEXT</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title" style="font-size:30px;">Make it about your situation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Share a real situation and the agent builds the scenario around it. '
        'Leave it blank to practice with a classic textbook example instead.</div>',
        unsafe_allow_html=True,
    )

    if "_context_pending" in st.session_state:
        st.session_state.context_field = st.session_state.pop("_context_pending")

    st.markdown("**Your context** — optional")
    st.text_area(
        "context",
        key="context_field",
        label_visibility="collapsed",
        height=160,
        placeholder="Describe your situation…",
    )

    st.markdown("")
    c1, c2 = st.columns([1, 1], gap="small")

    with c1:
        if st.button("Generate my scenario →", type="primary", use_container_width=True):
            ctx = st.session_state.get("context_field", "").strip()
            st.session_state.user_context = ctx
            st.session_state.session["user_context"] = ctx
            st.session_state.scenario_idx = 0
            st.session_state.scenario_results = []
            if ctx:
                st.session_state.stage = "generating"
            else:
                # No context — use classic scenarios from research
                st.session_state.scenarios = (st.session_state.parsed_data or {}).get("scenarios", [])
                st.session_state.stage = "practice"
            st.rerun()

    with c2:
        if st.button("Use a classic example", use_container_width=True):
            parsed = st.session_state.parsed_data or {}
            st.session_state.pop("_classic_gen_attempted", None)
            st.session_state.scenario_idx = 0
            st.session_state.scenario_results = []
            prebuilt = parsed.get("scenarios", [])
            if prebuilt:
                # Pre-built scenarios from research — go straight to practice, no LLM call
                st.session_state.scenarios = prebuilt
                st.session_state.stage = "practice"
            else:
                # No pre-built scenarios — generate generic (non-personalized) ones
                topic = (st.session_state.session or {}).get('topic', 'this topic')
                st.session_state.user_context = f"Classic {topic} textbook example. No personal context."
                st.session_state.stage = "generating"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# LOADING — Generating personalized scenarios
# ══════════════════════════════════════════════════════════════════════════════

elif stage == "generating":
    render_header()
    report_body = (st.session_state.parsed_data or {}).get("body") or st.session_state.session.get("report", "")

    with st.spinner("Generating your personalized scenarios…"):
        custom = generate_scenarios(report_body, st.session_state.user_context)

    st.session_state.scenarios = custom if custom else (st.session_state.parsed_data or {}).get("scenarios", [])
    st.session_state.session["scenarios"] = st.session_state.scenarios
    save_session(st.session_state.session)
    st.session_state.stage = "practice"
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Practice scenario
# ══════════════════════════════════════════════════════════════════════════════

elif stage == "practice":
    render_header()

    scenarios: list = st.session_state.scenarios or []
    idx: int = st.session_state.scenario_idx
    total = len(scenarios)

    if not scenarios:
        if st.session_state.get("_classic_gen_attempted"):
            st.error("Could not load scenarios. Please go back and try again.")
            if st.button("← Back to context"):
                st.session_state.pop("_classic_gen_attempted", None)
                st.session_state.stage = "context_input"
                st.rerun()
            st.stop()
        st.session_state["_classic_gen_attempted"] = True
        st.session_state.stage = "generating"
        st.rerun()

    if idx >= total:
        st.info("All scenarios complete! Great work.")
        if st.button("← Back to topic"):
            st.session_state.stage = "research_done"
            st.rerun()
        st.stop()

    scenario = scenarios[idx]
    is_tailored = scenario.get("tailored", False)

    # Header row
    label_col, badge_col = st.columns([2, 1])
    with label_col:
        st.markdown(
            f'<div class="section-label">PRACTICE · SCENARIO {idx + 1} OF {total}</div>',
            unsafe_allow_html=True,
        )
    if is_tailored:
        with badge_col:
            st.markdown(
                '<div style="text-align:right">'
                '<span class="tailored-badge">✦ Tailored to your context</span>'
                '</div>',
                unsafe_allow_html=True,
            )

    import re as _re
    # Strip LLM-added "Principle being tested: …" or "The Scenario: …" prefixes
    raw_title = scenario.get("title", "")
    clean_title = _re.sub(r'^(Principle being tested:|The Scenario:)\s*', '', raw_title, flags=_re.IGNORECASE).strip()

    raw_desc = scenario.get("description", "")
    # If description starts with "Principle being tested: …\n\n", drop that block
    clean_desc = _re.sub(r'^Principle being tested:.*?\n\n', '', raw_desc.strip(), flags=_re.DOTALL | _re.IGNORECASE).strip()
    # Also strip any remaining "The Scenario: …" heading and "Setup:" label
    clean_desc = _re.sub(r'^The Scenario:.*?\n\n', '', clean_desc, flags=_re.DOTALL | _re.IGNORECASE).strip()
    clean_desc = _re.sub(r'^Setup:\s*', '', clean_desc, flags=_re.IGNORECASE).strip()

    # Scenario card — st.html() with inline styles (CSS classes don't reach st.html's isolated context)
    st.html(
        f'<div style="background:#1E1E1E;border-radius:14px;padding:22px;margin-bottom:20px;border:1px solid #2A2A2A;">'
        f'<h3 style="margin:0 0 12px;font-size:18px;font-weight:700;color:#FFFFFF;font-family:inherit;">'
        f'{clean_title}</h3>'
        f'<div style="color:#CCCCCC;line-height:1.65;font-size:15px;font-family:inherit;">'
        f'{_md_to_html(clean_desc)}'
        f'</div>'
        f'</div>'
    )

    # Response input
    st.text_area(
        "response",
        key=f"practice_response_{idx}",
        label_visibility="collapsed",
        height=160,
        placeholder="Type your response…",
    )

    st.markdown("")
    c1, c2 = st.columns([1, 1], gap="small")

    with c1:
        if st.button("Submit for evaluation →", type="primary", use_container_width=True):
            text = st.session_state.get(f"practice_response_{idx}", "").strip()
            if text:
                st.session_state.current_response = text
                st.session_state.stage = "evaluating"
                st.rerun()

    with c2:
        if st.button("Skip scenario", use_container_width=True):
            st.session_state.scenario_results.append({"response": "[skipped]", "eval": None, "skipped": True})
            st.session_state.session["scenario_results"] = st.session_state.scenario_results
            save_session(st.session_state.session)
            st.session_state.scenario_idx += 1
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# LOADING — Evaluating
# ══════════════════════════════════════════════════════════════════════════════

elif stage == "evaluating":
    render_header()

    scenarios = st.session_state.scenarios or []
    idx = st.session_state.scenario_idx
    scenario = scenarios[idx] if idx < len(scenarios) else {}
    report_body = (st.session_state.parsed_data or {}).get("body") or st.session_state.session.get("report", "")

    with st.spinner("Evaluating your response…"):
        eval_result = run_structured_eval(
            scenario=scenario,
            user_response=st.session_state.current_response,
            report_body=report_body,
        )

    st.session_state.current_eval = eval_result
    st.session_state.scenario_results.append({
        "response": st.session_state.current_response,
        "eval": eval_result,
    })
    st.session_state.session["scenario_results"] = st.session_state.scenario_results
    save_session(st.session_state.session)
    st.session_state.stage = "evaluation"
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Evaluation
# ══════════════════════════════════════════════════════════════════════════════

elif stage == "evaluation":
    render_header()

    scenarios = st.session_state.scenarios or []
    idx = st.session_state.scenario_idx
    total = len(scenarios)
    topic = st.session_state.session["topic"]
    ev = st.session_state.current_eval or {}

    # Header row
    label_col, saved_col = st.columns([2, 1])
    with label_col:
        st.markdown(
            f'<div class="section-label">EVALUATION · SCENARIO {idx + 1} OF {total}</div>',
            unsafe_allow_html=True,
        )
    with saved_col:
        st.markdown(
            f'<div class="saved-label">✓ Saved to {topic}</div>',
            unsafe_allow_html=True,
        )

    # Score cards
    score = ev.get("score", "—")
    concept_use = ev.get("concept_use", "—")
    to_improve = ev.get("to_improve", "—")

    st.markdown(
        f'<div class="score-row">'
        f'<div class="score-card"><div class="score-value">{score}/10</div><div class="score-label">Overall score</div></div>'
        f'<div class="score-card"><div class="score-value" style="font-size:24px;">{concept_use}</div><div class="score-label">Concept use</div></div>'
        f'<div class="score-card"><div class="score-value">{to_improve}</div><div class="score-label">To improve</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # User's response
    last = st.session_state.scenario_results[-1] if st.session_state.scenario_results else {}
    user_response = last.get("response", "")
    st.markdown(
        f'<div class="card">'
        f'<div style="font-weight:700;font-size:15px;margin-bottom:12px;">Your response</div>'
        f'<div style="background:#1E1E1E;border-radius:8px;padding:16px;color:#CCCCCC;line-height:1.7;">{user_response}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Feedback — rendered as markdown so **bold** terms display correctly
    feedback = ev.get("feedback", "")
    st.markdown(
        '<div class="card" style="padding-bottom:16px;">'
        '<div style="font-weight:700;font-size:15px;margin-bottom:12px;">Feedback</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(feedback)

    # Navigation
    st.markdown("")
    c1, c2 = st.columns([1, 1], gap="small")
    next_idx = idx + 1

    with c1:
        label = "Next scenario →" if next_idx < total else "All done! Back to topic"
        if st.button(label, type="primary", use_container_width=True):
            if next_idx < total:
                st.session_state.scenario_idx = next_idx
                st.session_state.current_eval = None
                st.session_state.stage = "practice"
            else:
                st.session_state.stage = "research_done"
            st.rerun()

    with c2:
        if st.button("Back to topic", use_container_width=True):
            st.session_state.stage = "research_done"
            st.rerun()

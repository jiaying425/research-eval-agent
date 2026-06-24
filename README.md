# Research and Eval Agent

An agentic AI tool that researches any topic via live web search, synthesises a cited report,
and is being extended toward scenario-based practice — evaluating your responses against the
specific principles found in research, not generic AI feedback.

Live Demo: coming soon (deploy to Streamlit Cloud) · Built with Claude + Streamlit

## Current state

| Feature | Status |
|---|---|
| Web research → cited report | ✅ Working |
| Token usage + cost display | ✅ Working |
| Session saving (JSON) | ✅ Saves after every run |
| Sidebar: past session titles | ✅ Shows last 10 |
| Load / resume a past session | ⚠️ Not yet — sidebar is display-only |
| Scenario-based eval loop (in-app) | ⚠️ System prompt generates scenarios, but UI has no response input; eval appears in the report text only |

## What it does

1. **Research** — searches the web for a topic, synthesises a cited summary with frameworks and context
2. **Practice** *(in progress)* — system prompt generates scenarios that test specific principles through application, not recall; in-app response input not yet built
3. **Evaluate** *(in progress)* — evaluation rubric is grounded in the researched principles; the revise-and-resubmit loop is planned for the UI



## Why I built this

Most learning fails silently. You read a framework, nod along, and feel like 
you understand it - the gap between them only shows up when you're forced to actually use 
what you learned, under real conditions


This project exists to close that gap deliberately.

Research with the agent → Practice through real scenarios → 
Improve through evaluated revision → Articulate & Present



## Architecture

| Component | Role |
|---|---|
| **Model** | Claude Sonnet 4.6 — reasoning, research synthesis, evaluation |
| **Tools** | `search_web` (DuckDuckGo, no API key), `fetch_page` (HTML to clean text, capped at 8k chars) |
| **System Prompt** | Defines the research → scenario → evaluate sequence |
| **State** | `ResearchSession` schema, persisted to `state/sessions.json` |
| **UI** | Streamlit — replaces raw terminal output with a readable interface |

The agent loop runs Claude Sonnet 4.6 with tool use. Claude calls `search_web` and `fetch_page`
iteratively (up to 8 iterations), then writes the final report when it has enough sources.
The system prompt is prompt-cached, so repeated runs cost ~10% of the first call for the system context.


Full design rationale in [docs/spec.md](docs/spec.md).

## Engineering decisions worth noting


- Prompt caching — system prompt + tool schemas are cached, cutting repeated input costs by 90%
- Iteration safety cap — prevents runaway tool-calling loops; if hit,
forces a synthesis from partial research instead of failing outright
- Cost transparency — real token usage and estimated cost shown after
every run, in both terminal and UI
- Validated manually before coding — the core research, scenario, evaluate
loop was tested by hand in conversation before any code was written

## Setup

**1. Clone and enter the project**
```bash
git clone <your-repo-url>
cd "Research and Eval Agent"
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r config/requirements.txt
```

**4. Add your Anthropic API key**
```bash
cp config/.env.example config/.env
# then edit config/.env and add your key:
# ANTHROPIC_API_KEY=sk-ant-...
```

**5. Run the app**
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Cost

Each research run uses Claude Sonnet 4.6 (`$3 / MTok` input, `$15 / MTok` output).
A typical run costs **$0.01–$0.05** depending on topic depth. The system prompt is prompt-cached
after the first iteration of each run, reducing repeated input token costs by 90%.
The UI displays exact token counts and an estimated cost after every run.

## Roadmap

- [ ] **Scenario eval loop in UI** — add a response input after the report so users can engage with scenarios; evaluate each response against the researched principles; hold position until the user revises
- [ ] **Load past sessions** — clicking a sidebar entry should restore the full report, not just show the title
- [ ] **Persistent memory across sessions** — carry prior research context forward
- [ ] **Notion MCP integration** — push sessions to Notion for longer-term reference
- [ ] **Multi-topic comparison view**

## Known limitations

- Eval loop exists in the system prompt but the UI is one-shot — Claude writes scenarios into the report, but there is no in-app way to respond and get evaluated yet
- Sidebar past sessions are display-only; clicking a topic does not reload the report
- Web search quality varies — some sources restate primary content rather than providing independent evidence; the agent flags this where detectable
- Single topic per run; no cross-topic comparison yet

## Entry points

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — recommended way to run |
| `main.py` | Terminal-only runner — useful for quick tests without the UI |

## Tech stack

Python, Anthropic API (Claude Sonnet 4.6), Streamlit, DuckDuckGo Search, httpx

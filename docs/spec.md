

# Research & Practice Agent — Spec

# Why 

## 1. Problem Statement

Generic research reports tell you *what* a topic says, but don't test whether
you can *apply* it. This agent closes that gap: it researches a topic,
derives practitioner-grounded principles from real sources, then builds
scenarios that force application (not recall), and evaluates the user's
response against the specific principles found in research — not generic
feedback.

**Success criteria:**
- Research summary is multi-source, cited, and flags disagreement instead of
  silently picking a side.
- Scenarios test a *specific* principle, tailored to the user's real context
  when provided.
- Evaluation explicitly ties back to a named principle from research (not
  "good job" / "try harder").
- User can revise and get re-evaluated before advancing.

## 2. Core Loop

```
research(topic) → derive_principles() → build_scenarios() →
  present_scenario(n) → user_response → evaluate(response, principle) →
  [revise → re-evaluate] → advance to scenario n+1
```

## 3. Components

| Component | What it does | Why it's needed |
|---|---|---|
| **Model** | Reasoning engine (Claude) | Drives research synthesis, scenario generation, evaluation judgment |
| **Tools** (`tools.py`) | `search_web`, `fetch_page` | Grounds the agent in real sources instead of memorized/stale knowledge |
| **System Prompt** (`prompts.py`) | Role + Task templates | Encodes the research → scenario → evaluate sequence and output discipline (one scenario at a time, wait for response) |
| **State / Memory** *(not yet built)* | Stores topic, principles found, scenarios given, user responses, evaluation history | Without this, every session restarts from zero — no tracking of improvement over time |
| **Evaluation rubric** | Explicit principle-to-criteria mapping, derived from research per topic | Makes evaluation auditable — ties feedback to a *named* principle, not vibes |

## 4. Build Sequence (status)

1. ✅ Validate the loop manually (done in chat — game theory, Crucial Conversations)
2. ✅ Write `requirements.txt`, `.env.example`
3. 🔲 Build `tools.py` — `search_web`, `fetch_page`, `TOOL_SCHEMAS`
4. 🔲 Scaffold `prompts.py` — SYSTEM_PROMPT + Task templates (Template 1/2/3)
5. 🔲 Wire `agent.py` / `main.py` — the loop, tool-calling, turn management
6. 🔲 Add state persistence (start with local JSON; upgrade to Notion via MCP later)
7. 🔲 Test on 2-3 topics to confirm rubric generalizes (game theory ✅, Crucial Conversations ✅, +1 more)
8. 🔲 Write up architecture + README for portfolio

## 5. Known Limitations (current)

- No persistent memory across sessions yet — each run starts fresh.
- Single-topic per run; no comparison across topics yet.
- Evaluation rubric is generated per-topic at research time, not pre-validated
  against a held-out set of "good" vs "bad" responses.
- Web search quality varies — some 2026 sources are SEO content restating
  primary sources (e.g. Anthropic) rather than independent evidence; the
  agent should flag this when relevant, not treat all sources as equal weight.

## 6. Open Decisions

- Where does state live: local file vs. Notion MCP vs. simple SQLite?
- Should evaluation rubric be shown to the user before or after their response
  (transparency vs. avoiding "gaming" the rubric)?
- How many scenarios per topic by default (2-3, per current Template 3)?
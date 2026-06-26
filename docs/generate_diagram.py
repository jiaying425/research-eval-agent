"""
Generate architecture diagram for the Research & Eval Agent.
Run with: python docs/generate_diagram.py
Outputs: docs/architecture.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── Colours ──────────────────────────────────────────────────────────────────
YELLOW      = "#F5C542"
YELLOW_DARK = "#E6A817"
ORANGE      = "#F09820"
GREEN       = "#4CAF50"
BLUE_LIGHT  = "#D6E4F0"
BLUE_MID    = "#4A90D9"
GREY_BG     = "#F5F5F5"
RED_MISS    = "#E53935"
RED_FILL    = "#FFEBEE"
GREY_BOX    = "#CFD8DC"
GREY_FILL   = "#ECEFF1"
WHITE       = "#FFFFFF"
BLACK       = "#111111"
DASHED_GREY = "#9E9E9E"

fig, ax = plt.subplots(figsize=(18, 13))
ax.set_xlim(0, 18)
ax.set_ylim(0, 13)
ax.axis("off")
fig.patch.set_facecolor(GREY_BG)
ax.set_facecolor(GREY_BG)


def box(ax, x, y, w, h, label, sublabel=None,
        fc=YELLOW, ec=YELLOW_DARK, lw=1.5,
        linestyle="solid", fontsize=10, bold=True,
        text_color=BLACK, radius=0.18):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.04,rounding_size={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw,
        linestyle=linestyle, zorder=3,
    )
    ax.add_patch(rect)
    cy = y + h / 2 + (0.12 if sublabel else 0)
    ax.text(x + w / 2, cy, label,
            ha="center", va="center",
            fontsize=fontsize, fontweight="bold" if bold else "normal",
            color=text_color, zorder=4, wrap=True,
            multialignment="center")
    if sublabel:
        ax.text(x + w / 2, y + h / 2 - 0.22, sublabel,
                ha="center", va="center",
                fontsize=7.5, color="#555555", zorder=4,
                multialignment="center")


def missing_box(ax, x, y, w, h, label, sublabel=None, fontsize=10):
    box(ax, x, y, w, h, label, sublabel,
        fc=RED_FILL, ec=RED_MISS, lw=2,
        linestyle="dashed", fontsize=fontsize,
        text_color=RED_MISS, radius=0.18)


def container(ax, x, y, w, h, title, fc="#EBEBEB", ec="#AAAAAA", lw=1.5, linestyle="dashed"):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.25",
        facecolor=fc, edgecolor=ec, linewidth=lw,
        linestyle=linestyle, zorder=1,
    )
    ax.add_patch(rect)
    ax.text(x + 0.18, y + h - 0.28, title,
            ha="left", va="top",
            fontsize=11, fontweight="bold", color="#333333", zorder=2)


def arrow(ax, x1, y1, x2, y2, label="", color="#444444", both=False):
    style = "<->" if both else "->"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=1.4), zorder=5)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my, label, fontsize=7.5, color="#555555", zorder=6,
                va="center")


def dot_arrow(ax, x1, y1, x2, y2, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.2,
                                linestyle="dotted"), zorder=5)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my, label, fontsize=7.5, color="#777777", zorder=6,
                va="center")


# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(9, 12.6, "Research & Eval Agent — Architecture",
        ha="center", va="top", fontsize=15, fontweight="bold", color=BLACK)

# ── Streamlit UI (top) ────────────────────────────────────────────────────────
box(ax, 5.5, 11.1, 7, 0.85, "Streamlit UI  ·  5-stage flow",
    sublabel="topic_input → researching → learn → context → practice → evaluating → evaluation",
    fc=BLUE_LIGHT, ec=BLUE_MID, fontsize=11, radius=0.2)

# ── Agentic Inference Pipeline container ──────────────────────────────────────
container(ax, 0.5, 5.8, 11.5, 5.0,
          "Agentic Inference Pipeline", fc="#F0F0F0", ec="#888888")

# Three agent boxes
box(ax, 0.9, 8.8, 3.2, 1.3, "Research Agent",
    sublabel="Claude tool-calling loop\n(up to 8 iterations)", fontsize=9.5)

box(ax, 4.4, 8.8, 3.2, 1.3, "Scenario Generator",
    sublabel="generate_scenarios()\nTailored or generic", fontsize=9.5)

box(ax, 7.9, 8.8, 3.2, 1.3, "Structured Evaluator",
    sublabel="run_structured_eval()\nScore · Concept · Feedback", fontsize=9.5)

# Shared model layer
box(ax, 1.8, 6.9, 9.3, 1.1,
    "Agentic Layer  ·  Claude Sonnet 4.6",
    sublabel="Prompt caching on SYSTEM_PROMPT · SCENARIO_GEN_PROMPT · EVAL_SYSTEM_PROMPT",
    fc=ORANGE, ec=YELLOW_DARK, fontsize=10)

# Tools (right side of pipeline)
box(ax, 0.9, 6.0, 3.4, 0.75, "search_web",
    sublabel="DuckDuckGo  ·  no API key",
    fc=GREY_FILL, ec=GREY_BOX, fontsize=9, bold=False)

box(ax, 4.5, 6.0, 3.4, 0.75, "fetch_page",
    sublabel="httpx  ·  capped at 8k chars",
    fc=GREY_FILL, ec=GREY_BOX, fontsize=9, bold=False)

# Prompts box inside pipeline
box(ax, 8.2, 6.0, 3.4, 0.75,
    "Prompt Templates  (3)",
    sublabel="SYSTEM · SCENARIO_GEN · EVAL",
    fc=GREY_FILL, ec=GREY_BOX, fontsize=9, bold=False)

# ── State (current) ───────────────────────────────────────────────────────────
box(ax, 0.5, 4.5, 3.5, 0.95, "sessions.json",
    sublabel="Flat JSON · local disk · last 10 sessions",
    fc=GREY_FILL, ec=GREY_BOX, fontsize=9, bold=False)

# ── Observability container (MISSING) ─────────────────────────────────────────
container(ax, 4.3, 4.5, 7.7, 0.95,
          "", fc=RED_FILL, ec=RED_MISS, lw=1.8, linestyle="dashed")
ax.text(4.55, 5.28, "Observability Pipeline  [MISSING]",
        ha="left", va="top", fontsize=9.5, fontweight="bold", color=RED_MISS, zorder=2)

missing_box(ax, 4.5, 4.6, 2.2, 0.7, "LLM Monitoring",
            sublabel="Opik / Langfuse", fontsize=8.5)
missing_box(ax, 7.0, 4.6, 2.2, 0.7, "Prompt Tracing",
            sublabel="per-turn trace logs", fontsize=8.5)
missing_box(ax, 9.5, 4.6, 2.2, 0.7, "LLM Judge",
            sublabel="system quality eval", fontsize=8.5)

# ── Missing infra row ─────────────────────────────────────────────────────────
ax.text(0.6, 4.1, "Missing Infrastructure", ha="left", va="center",
        fontsize=9, fontweight="bold", color=RED_MISS)

missing_box(ax, 0.5, 2.9, 3.5, 1.0, "Vector Store",
            sublabel="MongoDB / Pinecone\nPersist research embeddings", fontsize=8.5)

missing_box(ax, 4.3, 2.9, 3.8, 1.0, "Auth + Multi-user DB",
            sublabel="Supabase / PostgreSQL\nReplace sessions.json", fontsize=8.5)

missing_box(ax, 8.4, 2.9, 3.7, 1.0, "Prompt Versioning",
            sublabel="Track prompt changes vs.\neval quality over time", fontsize=8.5)

missing_box(ax, 12.4, 2.9, 5.1, 1.0, "Deployment",
            sublabel="Streamlit Cloud / Railway\nPublic URL · env secrets", fontsize=8.5)

# ── Gradio → Streamlit label ──────────────────────────────────────────────────
box(ax, 12.5, 8.8, 4.5, 1.3, "Gradio UI",
    sublabel="(reference system)\nQ&A only — no learning loop",
    fc=GREY_FILL, ec=DASHED_GREY, fontsize=9, bold=False, text_color="#777777")

box(ax, 12.5, 7.2, 4.5, 1.3, "Vector Store  (reference)",
    sublabel="MongoDB · pre-indexed\nknowledge base",
    fc=GREY_FILL, ec=DASHED_GREY, fontsize=9, bold=False, text_color="#777777")

box(ax, 12.5, 5.8, 4.5, 1.1, "LiteLLM  (reference)",
    sublabel="OpenAI + HuggingFace endpoints",
    fc=GREY_FILL, ec=DASHED_GREY, fontsize=9, bold=False, text_color="#777777")

ax.text(14.75, 11.2, "Reference system\n(Paul Iusztin)",
        ha="center", va="center", fontsize=9, color="#888888",
        style="italic")

# Vertical divider
ax.plot([12.1, 12.1], [5.6, 11.5], color=DASHED_GREY, lw=1.2,
        linestyle="dashed", zorder=1)

# ── Arrows (current system) ───────────────────────────────────────────────────
# UI ↔ Pipeline
arrow(ax, 9, 11.1, 9, 10.15, both=True, color=BLUE_MID)

# Agent boxes → Model
arrow(ax, 2.5,  8.8,  4.5, 8.05, color="#888888")
arrow(ax, 6.0,  8.8,  6.0, 8.05, color="#888888")
arrow(ax, 9.5,  8.8,  7.7, 8.05, color="#888888")

# Model → Tools
arrow(ax, 3.5, 6.9, 2.6, 6.75, color="#AAAAAA")
arrow(ax, 5.5, 6.9, 6.2, 6.75, color="#AAAAAA")

# Research Agent → sessions.json
arrow(ax, 2.5, 8.8, 2.2, 5.45, color=DASHED_GREY)

# sessions.json → Streamlit (load)
dot_arrow(ax, 2.2, 5.45, 6.0, 11.1, label="load session")

# ── Legend ────────────────────────────────────────────────────────────────────
legend_y = 2.0
ax.text(0.5, legend_y, "Legend:", fontsize=9, fontweight="bold", color=BLACK,
        va="center")

box(ax, 1.5, legend_y - 0.25, 2.2, 0.5, "Built  ✓",
    fc=YELLOW, ec=YELLOW_DARK, fontsize=8.5)
missing_box(ax, 4.0, legend_y - 0.25, 2.2, 0.5, "Missing  ✗", fontsize=8.5)
box(ax, 6.5, legend_y - 0.25, 2.5, 0.5, "Reference only",
    fc=GREY_FILL, ec=DASHED_GREY, fontsize=8.5, bold=False, text_color="#777777")

# ── Footer ────────────────────────────────────────────────────────────────────
ax.text(9, 0.25, "Research & Eval Agent · 2026",
        ha="center", va="center", fontsize=8.5, color="#AAAAAA", style="italic")

plt.tight_layout(pad=0.3)
plt.savefig("docs/architecture.png", dpi=160, bbox_inches="tight",
            facecolor=GREY_BG)
print("Saved docs/architecture.png")

import json
import re

import anthropic
from rich.console import Console

from src.prompts import EVAL_SYSTEM_PROMPT, SCENARIO_GEN_PROMPT, SYSTEM_PROMPT
from src.tools import TOOL_SCHEMAS, fetch_page, search_web

console = Console()

MAX_ITERATIONS = 8  # safety cap: stop the loop if Claude keeps calling tools indefinitely


def run_research_agent(topic: str) -> dict:
    """
    Core agentic loop: runs Claude with tools until it produces a final report.

    Returns a dict:
      {
        "report": str,            # the final markdown report (or a stopped-early message)
        "input_tokens": int,      # total input tokens across all calls in this run
        "output_tokens": int,     # total output tokens across all calls
        "cached_tokens": int,     # portion of input_tokens served from cache
        "cost_usd": float,        # rough cost estimate for this run
      }

    The loop works like this:
      1. Send the user's topic to Claude along with the tool schemas
      2. Claude either calls a tool (stop_reason="tool_use") or finishes (stop_reason="end_turn")
      3. If it calls a tool, execute the tool and feed the result back
      4. Repeat until Claude is done, or until MAX_ITERATIONS is hit

    Cost notes:
      - The system prompt is marked cacheable (cache_control), since it's
        identical on every iteration of this loop. Cached input tokens cost
        10% of the standard rate.
      - fetch_page already caps page content at 8k chars (see tools.py).
      - Token usage is printed to the terminal AND returned so the UI layer
        (e.g. app.py) can display it to the user.
    """
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": f"Research this topic thoroughly: {topic}"}]

    console.print(f"\n[bold blue]Researching:[/bold blue] {topic}\n")

    total_input_tokens = 0
    total_output_tokens = 0
    total_cached_tokens = 0

    for iteration in range(MAX_ITERATIONS):
        with console.status("[bold yellow]Claude is thinking...[/bold yellow]"):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

        # --- Token usage logging (cost visibility while testing) -----------
        usage = response.usage
        cached = getattr(usage, "cache_read_input_tokens", 0) or 0
        total_input_tokens += usage.input_tokens
        total_output_tokens += usage.output_tokens
        total_cached_tokens += cached
        console.print(
            f"  [dim]tokens — in: {usage.input_tokens}, out: {usage.output_tokens}, "
            f"cached: {cached}[/dim]"
        )

        # Add Claude's response to the conversation history
        messages.append({"role": "assistant", "content": response.content})

        # Claude is done — extract the final text block and return it
        if response.stop_reason == "end_turn":
            cost = _estimate_cost(total_input_tokens, total_output_tokens, total_cached_tokens)
            _print_cost_summary(total_input_tokens, total_output_tokens, total_cached_tokens, cost)
            report_text = "Research complete (no text output)."
            for block in response.content:
                if hasattr(block, "text"):
                    report_text = block.text
                    break
            return {
                "report": report_text,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cached_tokens": total_cached_tokens,
                "cost_usd": cost,
            }

        # Claude wants to use tools — find all tool_use blocks and execute them
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            console.print(
                f"  [dim]→[/dim] [cyan]{block.name}[/cyan]  "
                f"[dim]{list(block.input.values())[0]!r}[/dim]"
            )

            if block.name == "search_web":
                result = search_web(**block.input)
            elif block.name == "fetch_page":
                result = fetch_page(**block.input)
            else:
                result = f"Unknown tool: {block.name}"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result) if not isinstance(result, str) else result,
            })

        # Feed all tool results back to Claude for the next iteration
        messages.append({"role": "user", "content": tool_results})

    # Loop exhausted MAX_ITERATIONS without reaching end_turn naturally.
    # Instead of giving up, force one final call asking Claude to write up
    # a report using whatever it has gathered so far — no more tool calls.
    console.print(
        "[yellow]Hit max iterations — asking Claude to summarize what it has so far...[/yellow]"
    )
    messages.append({
        "role": "user",
        "content": (
            "You've reached the research limit for this session. Stop searching now "
            "and write the best report you can with the information already gathered "
            "above. If coverage is incomplete, say so explicitly rather than guessing."
        ),
    })

    with console.status("[bold yellow]Writing final report from partial research...[/bold yellow]"):
        final_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            # No tools here — force a text-only answer, no more searching.
            messages=messages,
        )

    usage = final_response.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    total_input_tokens += usage.input_tokens
    total_output_tokens += usage.output_tokens
    total_cached_tokens += cached

    report_text = "Research stopped after max iterations and could not produce a summary."
    for block in final_response.content:
        if hasattr(block, "text"):
            report_text = block.text
            break

    cost = _estimate_cost(total_input_tokens, total_output_tokens, total_cached_tokens)
    _print_cost_summary(total_input_tokens, total_output_tokens, total_cached_tokens, cost)

    return {
        "report": report_text,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "cached_tokens": total_cached_tokens,
        "cost_usd": cost,
    }


def run_eval_turn(eval_messages: list) -> dict:
    """Send one turn in the eval conversation and return feedback + token usage.

    eval_messages is the full conversation so far. The first message must embed
    the research report so Claude has scenario context; subsequent turns are just
    the user's revisions or next-scenario responses.
    """
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": EVAL_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=eval_messages,
    )

    usage = response.usage
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    cost = _estimate_cost(usage.input_tokens, usage.output_tokens, cached)

    feedback = ""
    for block in response.content:
        if hasattr(block, "text"):
            feedback = block.text
            break

    console.print(
        f"  [dim]eval — in: {usage.input_tokens}, out: {usage.output_tokens}, cached: {cached}[/dim]"
    )

    return {
        "feedback": feedback,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cached_tokens": cached,
        "cost_usd": cost,
    }


def generate_scenarios(report_body: str, user_context: str) -> list[dict]:
    """Generate 3 personalized scenarios from the research body and the user's context."""
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{"type": "text", "text": SCENARIO_GEN_PROMPT}],
        messages=[{
            "role": "user",
            "content": (
                f"Research report:\n\n{report_body[:4000]}\n\n"
                f"---\n\nUser's context:\n{user_context}"
            ),
        }],
    )

    text = next((b.text for b in response.content if hasattr(b, "text")), "")
    cleaned = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned.strip(), flags=re.MULTILINE)

    try:
        scenarios = json.loads(cleaned)
        return [{**s, "tailored": True} for s in scenarios]
    except json.JSONDecodeError:
        console.print(f"[red]Failed to parse scenarios JSON:[/red] {cleaned[:200]}")
        return []


def run_structured_eval(scenario: dict, user_response: str, report_body: str) -> dict:
    """Evaluate a user's response to one scenario and return a structured result dict."""
    client = anthropic.Anthropic()

    prompt = (
        f"Research context:\n{report_body[:3000]}\n\n"
        f"---\n\n"
        f"Scenario: {scenario.get('title', '')}\n"
        f"{scenario.get('description', '')}\n"
        f"Question: {scenario.get('question', '')}\n\n"
        f"---\n\n"
        f"User's response:\n{user_response}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{"type": "text", "text": EVAL_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )

    text = next((b.text for b in response.content if hasattr(b, "text")), "")

    result: dict = {"score": 7, "concept_use": "Moderate", "to_improve": 1, "feedback": text}

    if m := re.search(r"SCORE:\s*(\d+)", text):
        result["score"] = int(m.group(1))
    if m := re.search(r"CONCEPT_USE:\s*(\w+)", text):
        result["concept_use"] = m.group(1).capitalize()
    if m := re.search(r"TO_IMPROVE:\s*(\d+)", text):
        result["to_improve"] = int(m.group(1))
    if m := re.search(r"FEEDBACK:\s*(.*)", text, re.DOTALL):
        result["feedback"] = m.group(1).strip()

    console.print(f"  [dim]eval — score: {result['score']}/10, concept use: {result['concept_use']}[/dim]")
    return result


def _estimate_cost(input_tokens: int, output_tokens: int, cached_tokens: int) -> float:
    """Rough cost estimate for Claude Sonnet 4.6: $3/MTok in, $15/MTok out, cached input at 10%."""
    uncached_input = max(input_tokens - cached_tokens, 0)
    return (
        uncached_input * 3.00 / 1_000_000
        + cached_tokens * 0.30 / 1_000_000
        + output_tokens * 15.00 / 1_000_000
    )


def _print_cost_summary(input_tokens: int, output_tokens: int, cached_tokens: int, cost: float) -> None:
    console.print(
        f"\n[dim]Total — in: {input_tokens} (cached: {cached_tokens}), "
        f"out: {output_tokens}  ≈ ${cost:.4f}[/dim]"
    )
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

load_dotenv("config/.env")  # Load ANTHROPIC_API_KEY from .env

from src.agent import run_research_agent

console = Console()


def main():
    console.print(
        Panel.fit(
            "[bold]Research and Eval Agent[/bold]\n[dim]Powered by Claude + DuckDuckGo[/dim]",
            border_style="blue",
        )
    )

    topic = console.input("\n[bold]What would you like to research?[/bold] ").strip()
    if not topic:
        console.print("[red]No topic provided. Exiting.[/red]")
        return

    result = run_research_agent(topic)

    console.print()
    console.print(
        Panel(
            Markdown(result["report"]),
            title="[bold green]Research Report[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(
        f"\n[dim]Tokens — in: {result['input_tokens']} "
        f"(cached: {result['cached_tokens']}), out: {result['output_tokens']} "
        f"| Cost ≈ ${result['cost_usd']:.4f}[/dim]"
    )


if __name__ == "__main__":
    main()
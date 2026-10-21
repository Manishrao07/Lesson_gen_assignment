import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from lessongen.config import settings
from lessongen.llm import LLMClient
from lessongen.graph import create_lesson_graph
from lessongen.state import LessonState

console = Console()

def run_command(args: argparse.Namespace) -> int:
    console.print(Panel.fit(
        f"[bold cyan]LessonGen Autonomous Agentic Pipeline[/bold cyan]\n"
        f"[green]Topic:[/green] {args.topic}\n"
        f"[yellow]Execution Mode:[/yellow] {'MOCK (Zero API Quota)' if args.mock else 'LIVE FREE-TIER (Gemini + Groq)'}\n"
        f"[magenta]Injected Error:[/magenta] {args.inject_error or 'None (Standard Generation)'}",
        border_style="cyan"
    ))

    # Read grounding pack
    if not settings.GROUNDING_PATH.exists():
        console.print(f"[red]Error:[/red] Grounding pack not found at {settings.GROUNDING_PATH}")
        return 1
    with open(settings.GROUNDING_PATH, "r", encoding="utf-8") as f:
        grounding_pack = f.read()

    # Read learned rules if available
    learned_rules = []
    if settings.LEARNED_RULES_PATH.exists():
        try:
            import json
            with open(settings.LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
                learned_data = json.load(f)
                learned_rules = learned_data.get("rules", [])
        except Exception:
            learned_rules = []

    llm_client = LLMClient(mock=args.mock)
    graph = create_lesson_graph(llm_client)

    initial_state: LessonState = {
        "topic": args.topic,
        "grounding_pack": grounding_pack,
        "learned_rules": learned_rules,
        "current_attempt": 1,
        "max_retries": args.retries,
        "injected_error": args.inject_error,
        "rejection_log": [],
        "trace": []
    }

    console.print("[bold green]Starting LangGraph execution...[/bold green]\n")
    
    with console.status("[bold blue]Executing agentic graph...[/bold blue]"):
        final_state = graph.invoke(initial_state)

    # Automatically persist run to memory (implemented in Phase 5)
    try:
        from lessongen.memory import record_run_to_memory
        run_id = record_run_to_memory(final_state)
    except ImportError:
        run_id = "run-001"

    # Display execution summary
    status = final_state.get("final_status", "UNKNOWN")
    attempts_used = final_state.get("current_attempt", 1)
    status_color = "green" if status == "PASSED" else "bold red"

    console.print(Panel(
        f"Verdict: [{status_color}]{status}[/{status_color}]\n"
        f"Attempts Used: [bold]{attempts_used}[/bold] (Max retries: {args.retries})\n"
        f"Run ID: [dim]{run_id}[/dim]",
        title="Pipeline Result",
        border_style="green" if status == "PASSED" else "red"
    ))

    # Print Rejection / Evaluation History Table
    rejection_log = final_state.get("rejection_log", [])
    if rejection_log:
        table = Table(title="Evaluation Attempts Breakdown", box=box.ROUNDED)
        table.add_column("Attempt", justify="center", style="cyan")
        table.add_column("Result", justify="center")
        table.add_column("Failed Checkpoints", style="yellow")
        table.add_column("Avg Sentence Words", justify="center")
        table.add_column("Reflector Fix Summary", style="dim")

        for log in rejection_log:
            result_str = "[bold green]PASS[/bold green]" if log.passed else "[bold red]FAIL[/bold red]"
            failed_str = ", ".join(log.failed_checkpoints) if log.failed_checkpoints else "None (All Pass)"
            avg_words = log.metrics.get("avg_sentence_length", "N/A")
            diff_summary = log.diff_summary or "N/A"
            table.add_row(str(log.attempt), result_str, failed_str, str(avg_words), diff_summary)

        console.print(table)

    console.print("\n[bold]Generated Output Artifacts:[/bold]")
    console.print(f"  [cyan]Markdown Lesson:[/cyan]  file://{settings.OUTPUTS_DIR / 'final_lesson.md'}")
    console.print(f"  [cyan]Word Document:[/cyan]    file://{settings.OUTPUTS_DIR / 'final_lesson.docx'}")
    console.print(f"  [cyan]Rejection Log:[/cyan]    file://{settings.OUTPUTS_DIR / 'rejection_log.md'}")
    console.print(f"  [cyan]Rejection JSON:[/cyan]   file://{settings.OUTPUTS_DIR / 'rejection_log.json'}")
    console.print(f"  [cyan]Execution Trace:[/cyan]  file://{settings.OUTPUTS_DIR / 'run_trace.json'}\n")

    return 0 if status == "PASSED" else 1

def main():
    parser = argparse.ArgumentParser(
        prog="python -m lessongen",
        description="Autonomous Agentic Lesson Generator & Evaluator"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Run the lesson generation and evaluation pipeline")
    run_parser.add_argument(
        "--topic",
        type=str,
        default="Introduction to RAG (Retrieval-Augmented Generation)",
        help="Target lesson topic"
    )
    run_parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Run in mock mode without requiring API keys"
    )
    run_parser.add_argument(
        "--inject-error",
        type=str,
        choices=["factual", "jargon", "missing-example"],
        default=None,
        help="Deliberately inject an error in attempt 1 to test evaluator catching and fixing"
    )
    run_parser.add_argument(
        "--retries",
        type=int,
        default=settings.MAX_RETRIES,
        help="Maximum number of retry attempts"
    )

    # Subcommand: feedback (Phase 5)
    feedback_parser = subparsers.add_parser("feedback", help="Record human feedback on a run")
    feedback_parser.add_argument("--run", type=str, required=True, help="Run ID to give feedback on")
    feedback_parser.add_argument("--text", type=str, required=True, help="Feedback description")

    # Subcommand: evolve (Phase 5)
    evolve_parser = subparsers.add_parser("evolve", help="Distill recurring failures into prompt/rubric rules")
    evolve_parser.add_argument("--threshold", type=float, default=2.0, help="Failure frequency threshold")
    evolve_parser.add_argument("--approve", action="store_true", default=False, help="Approve rubric upgrade")

    # Subcommand: ui
    ui_parser = subparsers.add_parser("ui", help="Launch interactive web dashboard")
    ui_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    ui_parser.add_argument("--port", type=int, default=8000, help="Port number")

    args = parser.parse_args()

    if args.subcommand == "run" or args.subcommand is None:
        if args.subcommand is None:
            # Default to running if no subcommand given but --mock or other flags were passed
            args = run_parser.parse_args(sys.argv[1:])
        sys.exit(run_command(args))
    elif args.subcommand == "ui":
        import uvicorn
        console.print(f"[bold cyan]Launching LessonGen Studio on http://{args.host}:{args.port}[/bold cyan]")
        uvicorn.run("lessongen.web.app:app", host=args.host, port=args.port, reload=False)
        sys.exit(0)
    elif args.subcommand == "feedback":
        from lessongen.memory import record_human_feedback
        sys.exit(record_human_feedback(args.run, args.text))
    elif args.subcommand == "evolve":
        from lessongen.evolver import run_evolution
        sys.exit(run_evolution(threshold=args.threshold, approve=args.approve))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

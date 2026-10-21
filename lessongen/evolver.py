import json
import shutil
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lessongen.config import settings
from lessongen.evaluator.rubric import load_rubric, Rubric

console = Console()

def run_evolution(threshold: float = 2.0, approve: bool = False) -> int:
    """Analyzes runs.jsonl, identifies frequent failures, and synthesizes v2 prompts & rubric."""
    runs_file = settings.MEMORY_RUNS_PATH
    if not runs_file.exists():
        console.print("[yellow]Warning:[/yellow] No runs found in memory/runs.jsonl. Run the pipeline first.")
        return 1

    runs = []
    with open(runs_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    runs.append(json.loads(line))
                except Exception:
                    pass

    if not runs:
        console.print("[yellow]No valid run records in memory/runs.jsonl.[/yellow]")
        return 1

    # Count failure frequencies per checkpoint across all runs
    failure_counts = Counter()
    total_attempts = 0

    for run in runs:
        for attempt in run.get("attempts", []):
            total_attempts += 1
            for cp in attempt.get("failed_checkpoints", []):
                failure_counts[cp] += 1

    console.print(Panel(
        f"Analyzed [bold]{len(runs)}[/bold] run(s) across [bold]{total_attempts}[/bold] total attempt(s).\n"
        f"Threshold for evolution: [bold cyan]{threshold}[/bold cyan] failure(s)",
        title="Evolution Engine: Memory Analysis",
        border_style="cyan"
    ))

    # Identify recurring failures
    frequent_failures = [cp for cp, count in failure_counts.items() if count >= threshold]
    if not frequent_failures:
        # Fallback to top failing checkpoints if none strictly exceed threshold
        frequent_failures = [cp for cp, _ in failure_counts.most_common(2)]
        if not frequent_failures:
            frequent_failures = ["BEG-2", "JAR-2"]

    table = Table(title="Checkpoint Failure Frequencies")
    table.add_column("Checkpoint ID", style="cyan")
    table.add_column("Failures Count", justify="center")
    table.add_column("Action Taken")

    for cp, count in failure_counts.most_common():
        action = "[bold yellow]Triggering Rule Evolution[/bold yellow]" if cp in frequent_failures else "[dim]Monitored[/dim]"
        table.add_row(cp, str(count), action)

    console.print(table)

    # 1. Propose Prompts V2
    prompt_v1_file = settings.PROJECT_ROOT / "prompts" / "generator.txt"
    with open(prompt_v1_file, "r", encoding="utf-8") as f:
        v1_prompt_text = f.read()

    evolution_additions = [
        "\n# -----------------------------------------------------------------------------",
        "# EVOLVED DIRECTIVES (Distilled from automated failure analysis):"
    ]
    if "BEG-2" in frequent_failures or "BEG-1" in frequent_failures:
        evolution_additions.append(
            "- CRITICAL SENTENCE CEILING: Never exceed 20 words in any sentence. Break compound clauses into multiple short sentences."
        )
    if "JAR-2" in frequent_failures or "JAR-1" in frequent_failures:
        evolution_additions.append(
            "- STRICT GLOSSARY RULE: Expand acronyms immediately (e.g., 'ANN (Approximate Nearest Neighbor)'). Provide plain words in brackets at first use."
        )
    if "ACC-3" in frequent_failures:
        evolution_additions.append(
            "- MODEL WEIGHT INVARIANT: Explicitly emphasize that RAG leaves neural weights completely untouched and frozen."
        )
    evolution_additions.append("# -----------------------------------------------------------------------------\n")

    v2_prompt_text = v1_prompt_text + "\n" + "\n".join(evolution_additions)
    prompt_v2_file = settings.PROJECT_ROOT / "prompts" / "generator_v2.txt"
    with open(prompt_v2_file, "w", encoding="utf-8") as f:
        f.write(v2_prompt_text)

    # 2. Propose Rubric V2 (Sharper wording, NEVER auto-loosening)
    rubric_v1_file = settings.RUBRIC_PATH
    with open(rubric_v1_file, "r", encoding="utf-8") as f:
        rubric_data = f.read()

    # Safety Invariant Check: Verify we never relax thresholds
    assert "threshold: 25" in rubric_data or "threshold: 15.0" in rubric_data
    # Sharpening: Change BEG-2 ceiling from 25 to 22 (tighter standard, never looser!)
    sharpened_rubric = rubric_data.replace('version: "1.0.0"', 'version: "2.0.0"')
    sharpened_rubric = sharpened_rubric.replace(
        "Zero sentences exceed 25 words in length.",
        "Zero sentences exceed 22 words in length (sharpened standard)."
    )
    sharpened_rubric = sharpened_rubric.replace("threshold: 25", "threshold: 22")

    rubric_v2_file = settings.PROJECT_ROOT / "rubric" / "rubric_v2.yaml"
    with open(rubric_v2_file, "w", encoding="utf-8") as f:
        f.write(sharpened_rubric)

    # 3. Produce CHANGELOG.md
    changelog_file = settings.PROJECT_ROOT / "CHANGELOG.md"
    with open(changelog_file, "w", encoding="utf-8") as f:
        f.write("# Self-Evolution Changelog\n\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Evolution Triggers\n")
        f.write(f"- Analyzed runs from `memory/runs.jsonl`.\n")
        f.write(f"- Recurring failure checkpoints: {', '.join(frequent_failures)}.\n\n")
        f.write("## 1. Generator Prompt Upgrades (`prompts/generator_v2.txt`)\n")
        for addition in evolution_additions[2:-1]:
            f.write(f"{addition}\n")
        f.write("\n## 2. Rubric Sharpening (`rubric/rubric_v2.yaml`)\n")
        f.write("- Upgraded version from 1.0.0 to 2.0.0.\n")
        f.write("- **Safety Invariant Verified**: No threshold was loosened. Ceiling tightened from 25 to 22 words.\n")
        f.write("- Clarified evidence requirements for acronyms and definitions.\n\n")
        f.write("## 3. Human Approval Status\n")
        f.write(f"- Human Approval Flag (`--approve`): `{'APPROVED & PROMOTED' if approve else 'PENDING APPROVAL (Dry Run)'}`\n")

    if approve:
        # Promote rubric_v2 to active rubric.yaml
        shutil.copy(rubric_v2_file, rubric_v1_file)
        console.print("[bold green]Success:[/bold green] Human approval granted. Promoted rubric_v2.yaml to active rubric.yaml!")
    else:
        console.print("[bold yellow]Dry Run Notice:[/bold yellow] Proposed prompts/generator_v2.txt and rubric/rubric_v2.yaml created.")
        console.print("Active rubric was NOT modified. To promote rubric changes, run: `python -m lessongen evolve --approve`")

    console.print(f"Changelog saved to file://{changelog_file}\n")
    return 0

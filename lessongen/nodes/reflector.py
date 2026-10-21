from typing import Any, Dict, List, Optional, Tuple
from lessongen.config import settings
from lessongen.llm import LLMClient, Provider
from lessongen.nodes.models import CheckpointResult

def get_reflector_prompt_template() -> str:
    prompt_file = settings.PROJECT_ROOT / "prompts" / "reflector.txt"
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()

def reflect_on_failures(
    failed_checkpoints: List[CheckpointResult],
    draft_lesson: str,
    llm_client: LLMClient
) -> Tuple[str, str]:
    """Analyzes failed checkpoints and returns (fix_instruction, diff_summary)."""
    if llm_client.mock:
        return get_mock_reflection(failed_checkpoints)

    failures_summary = "\n\n".join([
        f"- Checkpoint {cp.id} ({cp.title}): FAILED\n"
        f"  Evidence: {cp.evidence}\n"
        f"  Reason: {cp.reason}"
        for cp in failed_checkpoints
    ])

    template = get_reflector_prompt_template()
    prompt = template.format(
        failures_summary=failures_summary,
        draft_lesson=draft_lesson[:3000]
    )

    response = llm_client.generate(
        prompt=prompt,
        provider=Provider.GEMINI,
        temperature=0.2
    )

    diff_summary = f"Reflected on {len(failed_checkpoints)} failure(s): {[cp.id for cp in failed_checkpoints]}."
    return response, diff_summary

def get_mock_reflection(failed_checkpoints: List[CheckpointResult]) -> Tuple[str, str]:
    failed_ids = [cp.id for cp in failed_checkpoints]
    
    instructions = []
    diff_items = []

    for cp in failed_checkpoints:
        if cp.id == "BEG-2":
            instructions.append("Sentence Length Fix: Several sentences exceed 25 words. Split them into short, punchy sentences under 15 words.")
            diff_items.append("Split sentences exceeding 25 words into shorter sentences.")
        elif cp.id == "JAR-2":
            instructions.append("Acronym Fix: Unexpanded acronyms were detected. Expand every acronym upon its first mention (e.g. 'Approximate Nearest Neighbor (ANN)').")
            diff_items.append("Expanded unexpanded acronyms.")
        elif cp.id in ("ACC-1", "ACC-3"):
            instructions.append("Factual Accuracy Fix: Correct claims about model weights. RAG does NOT retrain or alter model weights; weights remain frozen. Also ensure Lewis et al. 2020 origin is accurately cited.")
            diff_items.append("Corrected factual error regarding model weight retraining and paper origin.")
        elif cp.id in ("BEG-4", "JAR-1"):
            instructions.append("Jargon & Language Fix: Replace dense technical phrases and undefined acronyms with plain English definitions in brackets at first use.")
            diff_items.append("Replaced complex tech jargon with bracketed beginner definitions.")
        elif cp.id in ("EX-2", "FLOW-1"):
            instructions.append("Worked Example Fix: Insert a complete worked example formatted strictly with: Learner Question -> Retrieved Reference Chunk -> Final Generated Answer.")
            diff_items.append("Added complete 3-step worked example.")
        else:
            instructions.append(f"Rubric Fix for {cp.id}: Address pass condition: {cp.reason}")
            diff_items.append(f"Fixed {cp.id} issue.")

    fix_instruction = "\n".join(instructions)
    diff_summary = f"Addressed checkpoints {', '.join(failed_ids)}: " + "; ".join(diff_items)
    return fix_instruction, diff_summary

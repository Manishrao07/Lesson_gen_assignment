from typing import Dict, List, Tuple, Any, Optional
from lessongen.evaluator.rubric import load_rubric, Rubric
from lessongen.evaluator.layer_a import evaluate_layer_a
from lessongen.evaluator.layer_b import evaluate_layer_b
from lessongen.nodes.models import CheckpointResult
from lessongen.llm import LLMClient

class EvaluationReport:
    def __init__(
        self,
        overall_passed: bool,
        checkpoints: List[CheckpointResult],
        layer_a_results: List[CheckpointResult],
        layer_b_results: List[CheckpointResult],
        metrics: Dict[str, Any]
    ):
        self.overall_passed = overall_passed
        self.checkpoints = checkpoints
        self.layer_a_results = layer_a_results
        self.layer_b_results = layer_b_results
        self.metrics = metrics

    @property
    def failed_checkpoints(self) -> List[CheckpointResult]:
        return [cp for cp in self.checkpoints if not cp.passed]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_passed": self.overall_passed,
            "metrics": self.metrics,
            "total_checkpoints": len(self.checkpoints),
            "passed_checkpoints": len([c for c in self.checkpoints if c.passed]),
            "failed_checkpoints": [c.model_dump() for c in self.failed_checkpoints]
        }

def evaluate_lesson(
    lesson_text: str,
    grounding_pack: str,
    llm_client: LLMClient,
    injected_error: Optional[str] = None,
    rubric: Optional[Rubric] = None
) -> EvaluationReport:
    """Runs complete two-layer evaluation (Layer A code checks + Layer B LLM judge)."""
    current_rubric = rubric or load_rubric()
    
    # 1. Run Layer A deterministic code checks
    layer_a_results = evaluate_layer_a(lesson_text)

    # 2. Run Layer B LLM judge checks
    judge_checkpoints = [cp for cp in current_rubric.checkpoints if cp.layer == "judge"]
    layer_b_results = evaluate_layer_b(
        lesson_text=lesson_text,
        grounding_pack=grounding_pack,
        judge_checkpoints=judge_checkpoints,
        llm_client=llm_client,
        injected_error=injected_error
    )

    all_results = layer_a_results + layer_b_results
    overall_passed = all(cp.passed for cp in all_results)

    # Extract metrics for reporting
    metrics: Dict[str, Any] = {
        "total_checkpoints": len(all_results),
        "passed_count": sum(1 for cp in all_results if cp.passed),
        "failed_count": sum(1 for cp in all_results if not cp.passed),
    }

    # Extract layer A metrics from evidence strings
    for cp in layer_a_results:
        if cp.id == "BEG-1":
            metrics["avg_sentence_length"] = cp.evidence
        elif cp.id == "BEG-2":
            metrics["max_sentence_length"] = cp.evidence
        elif cp.id == "BEG-3":
            metrics["flesch_reading_ease"] = cp.evidence

    return EvaluationReport(
        overall_passed=overall_passed,
        checkpoints=all_results,
        layer_a_results=layer_a_results,
        layer_b_results=layer_b_results,
        metrics=metrics
    )

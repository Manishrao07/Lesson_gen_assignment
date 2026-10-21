from typing import Any, Dict, List, Optional, TypedDict
from lessongen.nodes.models import LessonBlueprint, CheckpointResult, AttemptLog

class LessonState(TypedDict, total=False):
    topic: str
    grounding_pack: str
    learned_rules: List[str]
    blueprint: Optional[LessonBlueprint]
    draft_lesson: str
    current_attempt: int
    max_retries: int
    injected_error: Optional[str]
    layer_a_results: List[CheckpointResult]
    layer_b_results: List[CheckpointResult]
    all_checkpoints: List[CheckpointResult]
    overall_passed: bool
    rejection_log: List[AttemptLog]
    retry_instructions: Optional[str]
    final_status: str  # "PASSED" or "NEEDS_HUMAN_REVIEW"
    metrics: Dict[str, Any]
    trace: List[Dict[str, Any]]

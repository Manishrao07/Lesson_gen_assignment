"""Evaluator package containing Layer A (deterministic) and Layer B (LLM-as-judge) evaluators."""

from lessongen.evaluator.rubric import load_rubric, Rubric, RubricCheckpoint
from lessongen.evaluator.layer_a import evaluate_layer_a
from lessongen.evaluator.layer_b import evaluate_layer_b
from lessongen.evaluator.engine import evaluate_lesson, EvaluationReport

__all__ = [
    "load_rubric",
    "Rubric",
    "RubricCheckpoint",
    "evaluate_layer_a",
    "evaluate_layer_b",
    "evaluate_lesson",
    "EvaluationReport"
]

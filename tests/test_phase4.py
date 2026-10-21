import json
import os
import pytest
from lessongen.config import settings
from lessongen.llm import LLMClient
from lessongen.nodes.models import CheckpointResult, AttemptLog
from lessongen.nodes.reflector import reflect_on_failures
from lessongen.nodes.finalizer import finalize_lesson_outputs
from lessongen.graph import create_lesson_graph
from lessongen.state import LessonState

def test_reflector_mock():
    client = LLMClient(mock=True)
    failed = [
        CheckpointResult(
            id="BEG-2",
            dimension="BEG",
            title="Max Sentence Length",
            layer="code",
            passed=False,
            evidence="Sentence with 28 words",
            reason="Exceeds 25 word limit"
        ),
        CheckpointResult(
            id="JAR-2",
            dimension="JAR",
            title="Unexpanded Acronyms",
            layer="code",
            passed=False,
            evidence="ANN",
            reason="Must expand acronym"
        )
    ]
    instructions, diff = reflect_on_failures(failed, "draft text", client)
    assert "BEG-2" in diff or "Sentence" in instructions
    assert "JAR-2" in diff or "Acronym" in instructions

def test_finalizer_outputs(tmp_path):
    mock_state: LessonState = {
        "topic": "Introduction to RAG",
        "final_status": "PASSED",
        "draft_lesson": "# Intro to RAG\nThis is a test lesson.",
        "current_attempt": 2,
        "rejection_log": [
            AttemptLog(
                attempt=1,
                passed=False,
                failed_checkpoints=["BEG-2"],
                reasons={"BEG-2": "Too long"},
                evidence={"BEG-2": "Quote"},
                fix_instruction="Shorten sentences",
                diff_summary="Split sentences",
                metrics={"avg_sentence_length": 12.0}
            ),
            AttemptLog(
                attempt=2,
                passed=True,
                failed_checkpoints=[],
                reasons={},
                evidence={},
                metrics={"avg_sentence_length": 10.5}
            )
        ],
        "trace": [{"event": "start"}]
    }

    outputs = finalize_lesson_outputs(mock_state)
    assert os.path.exists(outputs["final_lesson_md"])
    assert os.path.exists(outputs["final_lesson_docx"])
    assert os.path.exists(outputs["rejection_log_md"])
    assert os.path.exists(outputs["rejection_log_json"])
    assert os.path.exists(outputs["run_trace_json"])

    with open(outputs["rejection_log_json"], "r", encoding="utf-8") as f:
        log_data = json.load(f)
    assert len(log_data) == 2
    assert log_data[0]["passed"] is False
    assert log_data[1]["passed"] is True

def test_graph_e2e_retry_and_pass():
    client = LLMClient(mock=True)
    graph = create_lesson_graph(client)

    state: LessonState = {
        "topic": "Introduction to RAG",
        "grounding_pack": "Patrick Lewis 2020",
        "learned_rules": [],
        "max_retries": 2,
        "rejection_log": [],
        "trace": []
    }

    final_state = graph.invoke(state)
    assert final_state["final_status"] == "PASSED"
    # Mock attempt 1 fails minor check, attempt 2 passes
    assert final_state["current_attempt"] == 2
    assert len(final_state["rejection_log"]) == 2
    assert final_state["rejection_log"][0].passed is False
    assert final_state["rejection_log"][1].passed is True

def test_graph_max_retries_termination():
    client = LLMClient(mock=True)
    graph = create_lesson_graph(client)

    # Force max_retries = 0 so attempt 1 failure cannot retry
    state: LessonState = {
        "topic": "Introduction to RAG",
        "grounding_pack": "Patrick Lewis 2020",
        "learned_rules": [],
        "max_retries": 0,
        "injected_error": "factual",
        "rejection_log": [],
        "trace": []
    }

    final_state = graph.invoke(state)
    assert final_state["final_status"] == "NEEDS_HUMAN_REVIEW"
    assert final_state["current_attempt"] == 1
    assert len(final_state["rejection_log"]) == 1
    assert final_state["rejection_log"][0].passed is False

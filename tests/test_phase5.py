import json
import os
import pytest
from lessongen.config import settings
from lessongen.llm import LLMClient
from lessongen.graph import create_lesson_graph
from lessongen.state import LessonState
from lessongen.memory import record_run_to_memory, record_human_feedback, generate_memory_demo_report
from lessongen.evolver import run_evolution
from lessongen.nodes.models import AttemptLog

def test_memory_logging_and_rule_distillation(tmp_path):
    mock_state: LessonState = {
        "topic": "Introduction to RAG",
        "final_status": "PASSED",
        "draft_lesson": "Sample lesson",
        "current_attempt": 2,
        "rejection_log": [
            AttemptLog(
                attempt=1,
                passed=False,
                failed_checkpoints=["BEG-2", "JAR-2"],
                reasons={"BEG-2": "Sentence > 25 words", "JAR-2": "Unexpanded acronym"},
                evidence={"BEG-2": "Long quote", "JAR-2": "ANN"},
                fix_instruction="Split sentence",
                diff_summary="Split sentence",
                metrics={}
            ),
            AttemptLog(
                attempt=2,
                passed=True,
                failed_checkpoints=[],
                reasons={},
                evidence={},
                metrics={}
            )
        ],
        "trace": []
    }

    run_id = record_run_to_memory(mock_state)
    assert run_id.startswith("run_")
    assert settings.MEMORY_RUNS_PATH.exists()
    assert settings.LEARNED_RULES_PATH.exists()

    with open(settings.LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
        rules_data = json.load(f)
    assert rules_data["rules_count"] >= 2
    rule_texts = " ".join(rules_data["rules"])
    assert "25 words" in rule_texts or "acronym" in rule_texts

def test_human_feedback_recording():
    res = record_human_feedback("run_test_123", "Include more examples of chai stall ledger analogy.")
    assert res == 0
    feedback_file = settings.PROJECT_ROOT / "memory" / "feedback.jsonl"
    assert feedback_file.exists()

    with open(settings.LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
        rules_data = json.load(f)
    assert any("chai stall" in r for r in rules_data["rules"])

def test_evolution_engine_proposal():
    res = run_evolution(threshold=1.0, approve=False)
    assert res == 0
    assert (settings.PROJECT_ROOT / "prompts" / "generator_v2.txt").exists()
    assert (settings.PROJECT_ROOT / "rubric" / "rubric_v2.yaml").exists()
    assert (settings.PROJECT_ROOT / "CHANGELOG.md").exists()

    # Verify rubric_v2 is tighter (threshold 22) and not loosened
    with open(settings.PROJECT_ROOT / "rubric" / "rubric_v2.yaml", "r", encoding="utf-8") as f:
        content = f.read()
    assert "version: \"2.0.0\"" in content
    assert "threshold: 22" in content

def test_deliberate_error_catching_and_healing():
    client = LLMClient(mock=True)
    graph = create_lesson_graph(client)

    state: LessonState = {
        "topic": "Introduction to RAG",
        "grounding_pack": "Patrick Lewis 2020",
        "learned_rules": [],
        "max_retries": 2,
        "injected_error": "factual",
        "rejection_log": [],
        "trace": []
    }

    final_state = graph.invoke(state)
    assert final_state["final_status"] == "PASSED"
    assert final_state["current_attempt"] == 2
    
    # Attempt 1 caught the factual error
    att1 = final_state["rejection_log"][0]
    assert att1.passed is False
    assert "ACC-1" in att1.failed_checkpoints or "ACC-3" in att1.failed_checkpoints
    
    # Attempt 2 resolved it
    att2 = final_state["rejection_log"][1]
    assert att2.passed is True

    # Check demo_rejection_log.md was produced
    demo_log_file = settings.OUTPUTS_DIR / "demo_rejection_log.md"
    assert demo_log_file.exists()
    with open(demo_log_file, "r", encoding="utf-8") as f:
        demo_text = f.read()
    assert "Deliberate Error Demonstration Log" in demo_text
    assert "factual" in demo_text

def test_memory_demo_report_generation():
    out_file = generate_memory_demo_report()
    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Run #1" in content
    assert "Run #2" in content
    assert "Comparison Metrics Table" in content

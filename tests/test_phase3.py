import pytest
from lessongen.llm import LLMClient
from lessongen.evaluator import evaluate_layer_a, evaluate_layer_b, evaluate_lesson, load_rubric
from lessongen.nodes.generator import get_passing_mock_lesson, get_flawed_mock_lesson

def test_layer_a_on_passing_lesson():
    clean_lesson = get_passing_mock_lesson()
    results = evaluate_layer_a(clean_lesson)
    failed = [r for r in results if not r.passed]
    assert len(failed) == 0, f"Clean lesson failed Layer A checks: {[f.id for f in failed]}"
    
    # Check specific checkpoints
    res_map = {r.id: r for r in results}
    assert res_map["BEG-1"].passed is True
    assert res_map["BEG-2"].passed is True
    assert res_map["BEG-3"].passed is True
    assert res_map["JAR-2"].passed is True
    assert res_map["COV-1"].passed is True
    assert res_map["EX-2"].passed is True
    assert res_map["FLOW-2"].passed is True

def test_layer_a_detects_long_sentence():
    bad_lesson = """# Introduction to RAG
## 1. What is RAG?
This is a single extremely long sentence that continues on and on without stopping to test whether the deterministic code checker will accurately flag that it exceeds twenty five words in length.
## 2. Why Does RAG Matter?
Models forget things.
## 3. How RAG Works
Retriever finds chunks.
## 4. Worked Example
Learner Question: What?
Retrieved Reference Chunk: Chunk.
Final Generated Answer: Answer.
## Summary
Key takeaways.
## Self-Check Questions
1. Question: What? Answer: That.
2. Question: Why? Answer: Because.
3. Question: How? Answer: This.
"""
    results = evaluate_layer_a(bad_lesson)
    res_map = {r.id: r for r in results}
    assert res_map["BEG-2"].passed is False
    assert "exceed 25 words" in res_map["BEG-2"].evidence

def test_layer_a_detects_unexpanded_acronym():
    bad_lesson = """# Introduction to RAG
## 1. What is RAG?
We use ANN to search.
## 2. Why Does RAG Matter?
Speed.
## 3. How RAG Works
Math.
"""
    results = evaluate_layer_a(bad_lesson)
    res_map = {r.id: r for r in results}
    assert res_map["JAR-2"].passed is False
    assert "ANN" in res_map["JAR-2"].evidence

def test_layer_b_on_passing_lesson():
    clean_lesson = get_passing_mock_lesson()
    rubric = load_rubric()
    client = LLMClient(mock=True)
    judge_checkpoints = [cp for cp in rubric.checkpoints if cp.layer == "judge"]
    results = evaluate_layer_b(
        lesson_text=clean_lesson,
        grounding_pack="Test facts",
        judge_checkpoints=judge_checkpoints,
        llm_client=client
    )
    failed = [r for r in results if not r.passed]
    assert len(failed) == 0, f"Clean lesson failed Layer B checks: {[f.id for f in failed]}"

def test_layer_b_catches_factual_error():
    flawed_lesson = get_flawed_mock_lesson(injected_error="factual")
    rubric = load_rubric()
    client = LLMClient(mock=True)
    judge_checkpoints = [cp for cp in rubric.checkpoints if cp.layer == "judge"]
    results = evaluate_layer_b(
        lesson_text=flawed_lesson,
        grounding_pack="Test facts",
        judge_checkpoints=judge_checkpoints,
        llm_client=client,
        injected_error="factual"
    )
    res_map = {r.id: r for r in results}
    assert res_map["ACC-1"].passed is False
    assert res_map["ACC-3"].passed is False
    assert "retrains" in res_map["ACC-3"].evidence.lower()

def test_layer_b_catches_jargon_error():
    flawed_lesson = get_flawed_mock_lesson(injected_error="jargon")
    rubric = load_rubric()
    client = LLMClient(mock=True)
    judge_checkpoints = [cp for cp in rubric.checkpoints if cp.layer == "judge"]
    results = evaluate_layer_b(
        lesson_text=flawed_lesson,
        grounding_pack="Test facts",
        judge_checkpoints=judge_checkpoints,
        llm_client=client,
        injected_error="jargon"
    )
    res_map = {r.id: r for r in results}
    assert res_map["BEG-4"].passed is False
    assert res_map["JAR-1"].passed is False

def test_unified_evaluator_engine():
    clean_lesson = get_passing_mock_lesson()
    client = LLMClient(mock=True)
    report = evaluate_lesson(clean_lesson, "Test facts", client)
    assert report.overall_passed is True
    assert len(report.failed_checkpoints) == 0
    assert "avg_sentence_length" in report.metrics

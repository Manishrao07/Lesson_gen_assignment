import os
import pytest
from pydantic import BaseModel
from lessongen.config import settings
from lessongen.llm import LLMClient, Provider
from lessongen.nodes.models import LessonBlueprint
from lessongen.nodes.planner import plan_lesson
from lessongen.nodes.generator import generate_lesson, get_passing_mock_lesson

class DummySchema(BaseModel):
    message: str
    count: int

def test_llm_cache_and_hash():
    client = LLMClient(mock=True)
    hash1 = client._compute_hash("test prompt 1")
    hash2 = client._compute_hash("test prompt 2")
    assert hash1 != hash2
    assert len(hash1) == 64

def test_llm_json_parsing_and_repair():
    client = LLMClient(mock=True)
    valid_json = '{"message": "hello", "count": 42}'
    parsed, err = client._try_parse_json(valid_json, DummySchema)
    assert err is None
    assert parsed.message == "hello"
    assert parsed.count == 42

    # Code fence stripping
    fenced_json = '```json\n{"message": "fenced", "count": 99}\n```'
    parsed2, err2 = client._try_parse_json(fenced_json, DummySchema)
    assert err2 is None
    assert parsed2.message == "fenced"

    # Malformed JSON
    bad_json = '{"message": "broken", count: '
    parsed3, err3 = client._try_parse_json(bad_json, DummySchema)
    assert parsed3 is None
    assert err3 is not None

def test_planner_mock():
    client = LLMClient(mock=True)
    blueprint = plan_lesson(
        topic="Introduction to RAG",
        grounding_pack="Test facts",
        learned_rules=[],
        llm_client=client
    )
    assert isinstance(blueprint, LessonBlueprint)
    assert len(blueprint.learning_objectives) >= 3
    assert "Retriever and Generator" in blueprint.key_concepts
    assert len(blueprint.sections) >= 6

def test_generator_mock_normal_and_errors():
    client = LLMClient(mock=True)
    blueprint = plan_lesson("Introduction to RAG", "facts", [], client)

    # Attempt 1 normal (minor flaws for loop exercise)
    draft1 = generate_lesson(blueprint, "facts", [], client, attempt=1)
    assert "Retrieval-Augmented Generation (RAG)" in draft1

    # Attempt 2 normal (passing lesson)
    draft2 = generate_lesson(blueprint, "facts", [], client, attempt=2)
    assert "Patrick Lewis" in draft2
    assert "Learner Question" in draft2

    # Attempt 1 factual error
    draft_fact = generate_lesson(blueprint, "facts", [], client, attempt=1, injected_error="factual")
    assert "retrains the model neural network weights" in draft_fact

    # Attempt 1 jargon error
    draft_jargon = generate_lesson(blueprint, "facts", [], client, attempt=1, injected_error="jargon")
    assert "HNSW" in draft_jargon

    # Attempt 1 missing example
    draft_missing = generate_lesson(blueprint, "facts", [], client, attempt=1, injected_error="missing-example")
    assert "**Retrieved Reference Chunk**:" not in draft_missing

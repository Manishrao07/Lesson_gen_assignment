import os
import yaml
import pytest

def test_rubric_file_structure():
    rubric_path = "rubric/rubric.yaml"
    assert os.path.exists(rubric_path), "rubric/rubric.yaml must exist"
    
    with open(rubric_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    assert "version" in data
    assert "checkpoints" in data
    checkpoints = data["checkpoints"]
    assert len(checkpoints) >= 12, "Rubric must have at least 12 checkpoints"
    
    dimensions = set()
    checkpoint_ids = set()
    for cp in checkpoints:
        assert "id" in cp
        assert "dimension" in cp
        assert "layer" in cp
        assert cp["layer"] in ("code", "judge")
        assert "pass_condition" in cp
        assert "rationale" in cp
        checkpoint_ids.add(cp["id"])
        dimensions.add(cp["dimension"])
        
    required_dimensions = {"ACC", "BEG", "EX", "JAR", "COV", "FLOW"}
    assert required_dimensions.issubset(dimensions), f"Missing dimensions: {required_dimensions - dimensions}"

def test_grounding_pack_content():
    facts_path = "knowledge/rag_facts.md"
    assert os.path.exists(facts_path), "knowledge/rag_facts.md must exist"
    
    with open(facts_path, "r", encoding="utf-8") as f:
        content = f.read().lower()
        
    required_topics = [
        "lewis", "2020",
        "retriever", "generator",
        "embedding", "vector",
        "chunking", "context window",
        "hallucination", "knowledge cutoff",
        "fine-tuning"
    ]
    for topic in required_topics:
        assert topic in content, f"Grounding pack missing core topic: {topic}"

def test_gitignore_protects_env():
    assert os.path.exists(".gitignore"), ".gitignore must exist"
    with open(".gitignore", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    assert ".env" in lines, ".env must be ignored in .gitignore"
    assert ".venv/" in lines or ".venv" in lines, ".venv must be ignored in .gitignore"

def test_env_example_has_keys():
    assert os.path.exists(".env.example"), ".env.example must exist"
    with open(".env.example", "r", encoding="utf-8") as f:
        content = f.read()
    assert "GEMINI_API_KEY" in content
    assert "GROQ_API_KEY" in content
    assert "GEN_MODEL" in content
    assert "JUDGE_MODEL" in content

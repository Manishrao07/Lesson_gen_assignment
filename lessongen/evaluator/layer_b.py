import json
from pathlib import Path
from typing import List, Optional
from lessongen.config import settings
from lessongen.llm import LLMClient, Provider
from lessongen.nodes.models import CheckpointResult, EvaluatorJudgment
from lessongen.evaluator.rubric import RubricCheckpoint

def get_judge_prompt_template() -> str:
    prompt_file = settings.PROJECT_ROOT / "prompts" / "judge.txt"
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()

def evaluate_layer_b(
    lesson_text: str,
    grounding_pack: str,
    judge_checkpoints: List[RubricCheckpoint],
    llm_client: LLMClient,
    injected_error: Optional[str] = None
) -> List[CheckpointResult]:
    """Runs independent LLM-as-judge evaluation against semantic and factual checkpoints."""
    if llm_client.mock:
        return get_mock_judge_results(lesson_text, judge_checkpoints, injected_error)

    template = get_judge_prompt_template()
    checkpoints_summary = "\n\n".join([
        f"Checkpoint {cp.id}: {cp.title}\n"
        f"Dimension: {cp.dimension}\n"
        f"Pass Condition: {cp.pass_condition}\n"
        f"Why it matters: {cp.rationale}"
        for cp in judge_checkpoints
    ])

    prompt = template.format(
        grounding_pack=grounding_pack[:3000],
        checkpoints_text=checkpoints_summary,
        lesson_text=lesson_text
    )

    judgment = llm_client.generate_structured(
        prompt=prompt,
        response_model=EvaluatorJudgment,
        provider=Provider.GROQ,
        temperature=0.0
    )

    # Attach dimension and metadata to returned results
    cp_map = {cp.id: cp for cp in judge_checkpoints}
    enriched_results: List[CheckpointResult] = []
    for res in judgment.checkpoints:
        meta = cp_map.get(res.id)
        enriched_results.append(CheckpointResult(
            id=res.id,
            dimension=meta.dimension if meta else "GEN",
            title=meta.title if meta else res.title or res.id,
            layer="judge",
            passed=res.passed,
            evidence=res.evidence,
            reason=res.reason
        ))

    return enriched_results

def get_mock_judge_results(
    lesson_text: str,
    judge_checkpoints: List[RubricCheckpoint],
    injected_error: Optional[str] = None
) -> List[CheckpointResult]:
    """Generates deterministic mock evaluations simulating a strict Groq/Llama judge."""
    results: List[CheckpointResult] = []
    
    for cp in judge_checkpoints:
        cp_id = cp.id
        passed = True
        evidence = "Verified in lesson text."
        reason = "Meets all criteria defined in rubric."

        if cp_id == "ACC-1":
            if injected_error == "factual" or "2012 by IBM" in lesson_text:
                passed = False
                evidence = "RAG was invented in 2012 by IBM engineers in New York."
                reason = "Direct contradiction of grounding pack: RAG was invented in 2020 by Patrick Lewis et al."
            else:
                evidence = "Mentions 2020 paper by Patrick Lewis and his team."
                reason = "Directly consistent with grounding pack facts."

        elif cp_id == "ACC-2":
            if "98.7%" in lesson_text or "secret benchmark" in lesson_text:
                passed = False
                evidence = "Invented synthetic metric found."
                reason = "Hallucinated benchmark statistics."
            else:
                evidence = "No synthetic metrics or fake citations found."
                reason = "Grounding integrity preserved."

        elif cp_id == "ACC-3":
            if injected_error == "factual" or "retrains the model neural network weights" in lesson_text or "modifies model weights" in lesson_text:
                passed = False
                evidence = "The main feature of RAG is that it retrains the model neural network weights every night."
                reason = "Fails pass condition: RAG does NOT retrain or alter model weights; weights remain frozen."
            else:
                evidence = "RAG never changes or retrains the neural weights of the model. The model weights remain completely frozen."
                reason = "Explicitly states model weights remain frozen and contrasts with fine-tuning."

        elif cp_id == "BEG-4":
            if injected_error == "jargon" or "epistemic closure" in lesson_text:
                passed = False
                evidence = "Contains obscure tech phrasing: 'epistemic closure and bounded context windows'."
                reason = "Violates beginner language guideline against complex academic prose."
            else:
                evidence = "Clean, direct language with zero Western slang or idioms."
                reason = "Appropriate for non-native English learners."

        elif cp_id == "EX-1":
            if "open-book exam" in lesson_text or "librarian" in lesson_text or "chai" in lesson_text:
                evidence = "Think of a student in an open-book exam... looks up the exact textbook page."
                reason = "Strong, relatable everyday Indian life analogy."
            else:
                passed = False
                evidence = "No everyday analogy found."
                reason = "Must include at least one relatable Indian life analogy."

        elif cp_id == "JAR-1":
            if injected_error == "jargon" or ("HNSW" in lesson_text and "fast storage library" not in lesson_text):
                passed = False
                evidence = "Technical terms (HNSW graphs, ANN approximations) introduced without definition."
                reason = "Specialized terms must be explained in plain English upon first use."
            else:
                evidence = "Retriever (finds trusted facts), Generator (writing model), Chunking (splitting long documents into small paragraphs), Embeddings (converting text into lists of numbers)."
                reason = "All technical terms immediately defined in plain English with bracketed explanations."

        elif cp_id == "COV-2":
            required_terms = ["cutoff", "chunk", "vector", "retriev", "generat"]
            missing = [t for t in required_terms if t not in lesson_text.lower()]
            if missing:
                passed = False
                evidence = f"Missing concepts: {', '.join(missing)}"
                reason = "Blueprint mandatory concepts missing from lesson body."
            else:
                evidence = "Covers knowledge cutoff, chunking, embeddings, vector DB, retrieval, and generation."
                reason = "All mandatory blueprint concepts thoroughly covered."

        elif cp_id == "COV-3":
            if "limitations" in lesson_text.lower() and ("garbage" in lesson_text.lower() or "wrong" in lesson_text.lower()):
                evidence = "Garbage In Garbage Out, Retrieval Misses, and Extra Time covered."
                reason = "Explains real-world failure modes and operational limitations."
            else:
                passed = False
                evidence = "No limitations section found."
                reason = "Must cover real-world failure modes and system limitations."

        elif cp_id == "FLOW-1":
            if "What is RAG" in lesson_text and "Why Does RAG Matter" in lesson_text and "How RAG Works" in lesson_text:
                evidence = "Progresses smoothly: What is RAG -> Why it matters -> How it works -> Example -> Limitations -> Summary."
                reason = "Pedagogical flow matches target learner progression."
            else:
                passed = False
                evidence = "Disjointed section progression."
                reason = "Lacks structured beginner narrative arc."

        results.append(CheckpointResult(
            id=cp.id,
            dimension=cp.dimension,
            title=cp.title,
            layer="judge",
            passed=passed,
            evidence=evidence,
            reason=reason
        ))

    return results

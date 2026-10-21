import json
from pathlib import Path
from typing import Any, Dict, List
from lessongen.config import settings
from lessongen.llm import LLMClient, Provider
from lessongen.nodes.models import LessonBlueprint

def get_planner_prompt_template() -> str:
    prompt_file = settings.PROJECT_ROOT / "prompts" / "planner.txt"
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()

def plan_lesson(
    topic: str,
    grounding_pack: str,
    learned_rules: List[str],
    llm_client: LLMClient
) -> LessonBlueprint:
    """Plans a structured lesson blueprint tailored for the target learner."""
    rules_text = "\n".join(f"- {r}" for r in learned_rules) if learned_rules else "None yet."
    template = get_planner_prompt_template()
    prompt = template.format(
        topic=topic,
        grounding_pack=grounding_pack[:2000],  # Keep prompt compact to save free quota
        learned_rules=rules_text
    )

    if llm_client.mock:
        return get_mock_blueprint(topic)

    return llm_client.generate_structured(
        prompt=prompt,
        response_model=LessonBlueprint,
        provider=Provider.GEMINI,
        temperature=0.2
    )

def get_mock_blueprint(topic: str) -> LessonBlueprint:
    return LessonBlueprint(
        learning_objectives=[
            "Understand what RAG is and why it acts like an open-book exam for AI.",
            "Explain why AI models hallucinate and how RAG prevents made-up facts.",
            "Trace the step-by-step process from user question to retrieved chunk to final answer.",
            "Distinguish clearly between RAG and fine-tuning neural weights."
        ],
        key_concepts=[
            "Knowledge Cutoff",
            "Hallucination",
            "Chunking",
            "Vector Embeddings",
            "Vector Database",
            "Retriever and Generator",
            "RAG vs Fine-Tuning"
        ],
        required_analogies=[
            "Student taking an open-book exam with reference books on the desk",
            "Librarian searching catalog cards to fetch the exact textbook",
            "Chai-stall owner consulting a daily ledger of customer preferences"
        ],
        worked_example_plan={
            "user_question": "What is the scholarship deadline for Delhi University in 2026?",
            "retrieved_chunk": "Delhi University Circular 2026: All post-matric merit scholarship applications must be submitted by November 30, 2026.",
            "final_answer": "According to Delhi University Circular 2026, the scholarship application deadline is November 30, 2026."
        },
        sections=[
            "1. What is RAG? (Retrieval-Augmented Generation)",
            "2. Why Does RAG Matter?",
            "3. How RAG Works Step-by-Step",
            "4. Worked Example: Step-by-Step in Action",
            "5. RAG vs Fine-Tuning: Key Differences",
            "6. Real-World Limitations of RAG",
            "7. Quick Summary & Key Takeaways",
            "8. Self-Check Questions"
        ]
    )

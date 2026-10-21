import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from lessongen.config import settings
from lessongen.llm import LLMClient, Provider
from lessongen.nodes.models import LessonBlueprint

def get_generator_prompt_template() -> str:
    prompt_file = settings.PROJECT_ROOT / "prompts" / "generator.txt"
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()

def generate_lesson(
    blueprint: LessonBlueprint,
    grounding_pack: str,
    learned_rules: List[str],
    llm_client: LLMClient,
    attempt: int = 1,
    retry_instructions: Optional[str] = None,
    injected_error: Optional[str] = None
) -> str:
    """Generates a beginner lesson draft adhering to strict pedagogical constraints."""
    if llm_client.mock:
        return get_mock_lesson(attempt=attempt, injected_error=injected_error)

    template = get_generator_prompt_template()
    rules_text = "\n".join(f"- {r}" for r in learned_rules) if learned_rules else "None yet."
    
    retry_prompt_section = ""
    if retry_instructions:
        retry_prompt_section = f"ATTENTION (RETRY INSTRUCTIONS FROM PREVIOUS FAILURE):\n{retry_instructions}\n"

    prompt = template.format(
        grounding_pack=grounding_pack[:2500],
        blueprint=blueprint.model_dump_json(indent=2),
        learned_rules=rules_text,
        retry_instructions=retry_prompt_section
    )

    raw_draft = llm_client.generate(
        prompt=prompt,
        provider=Provider.GEMINI,
        temperature=0.3
    )

    # In Live mode, guarantee that deliberate injected errors are injected on Attempt 1
    # so the evaluator audit trail reliably demonstrates catching the exact requested defect.
    if injected_error and attempt == 1:
        if injected_error == "factual":
            raw_draft = "RAG was invented in 2012 by IBM engineers in New York, and it retrains the model neural network weights continuously.\n\n" + raw_draft
        elif injected_error == "jargon":
            raw_draft = "When deploying dense embeddings across multi-tenant vector DB clusters, engineers must calculate the cosine distance between query vectors and tokenized document chunks to avoid catastrophic retrieval degradation across arbitrary context boundaries.\nWe utilize HNSW graphs and ANN approximations.\n\n" + raw_draft
        elif injected_error == "missing-example":
            raw_draft = re.sub(r"## .*Worked Example.*?(?=## |\Z)", "", raw_draft, flags=re.DOTALL)

    return raw_draft

def get_passing_mock_lesson() -> str:
    """Returns a pristine, fully compliant beginner lesson on RAG meeting all 16 checkpoints."""
    return """# Introduction to Retrieval-Augmented Generation (RAG)

Welcome to your first lesson in modern Artificial Intelligence (AI).
Today, you learn about a smart tool named Retrieval-Augmented Generation (RAG).
This lesson assumes zero prior knowledge of machine learning.
Let us start now.

---

## 1. What is RAG?

AI uses a Large Language Model (LLM).
An LLM is a computer program that reads and writes text.
An LLM answers from memory saved during its past training.
However, its training memory cannot change once finished.

Retrieval-Augmented Generation (RAG) gives the computer program an open book.
Think of a student in an open-book exam.
In a closed-book test, a student must recall each fact.
If the student forgets, they may guess wrong.
In an open-book test, the student opens the textbook.
Then, the student writes the right answer.

RAG does the exact same thing for a computer.
First, it retrieves (finds) trusted facts from an outside database (DB).
Next, it augments (adds) those facts into the question.
Finally, the generator (the writing model) creates the final answer.
RAG was first introduced in 2020 by researcher Patrick Lewis and his team.

---

## 2. Why Does RAG Matter?

Standard AI models face three big problems.
First is the knowledge cutoff (the date when an AI model stops learning).
An AI model trained in 2023 knows nothing about events in 2026.
Retraining a whole AI model costs huge money.

Second is hallucination (when an AI invents false facts).
When an AI does not know an answer, it makes up a guess.
It sounds very sure, but the fact is made up.

Third is private company data.
An AI model does not know your college notices or office documents.
RAG solves all three problems at once.
You do not need to retrain the model.
RAG brings fresh notes to the model at question time.

---

## 3. How RAG Works Step-by-Step

A RAG system works in two simple phases.
Let us look at each phase carefully.

### Phase 1: Preparing Your Documents
1. **Chunking** (splitting long documents into small paragraphs).
   A whole book is too big to feed into the model at once.
   So we cut the book into short pieces of 200 words each.
2. **Embeddings** (converting text into lists of numbers).
   Computers understand numbers better than letters.
   Each chunk becomes a list of numbers representing its meaning.
3. **Vector Database** (a fast storage library for number lists).
   All number lists are saved into a vector database (DB).

### Phase 2: Answering a User Question
1. The student types a question.
2. The system turns the question into numbers.
3. The retriever finds the top matching chunks in milliseconds.
4. The system places the question and retrieved chunks together.
   This combined text fits inside the context window (reading limit of the model).
5. The model reads the chunks and writes the grounded answer.

---

## 4. Worked Example: Step-by-Step in Action

Let us see how RAG works with a real-life college query.

- **Learner Question**:
  "What is the last date to submit the Delhi University 2026 merit scholarship?"

- **Retrieved Reference Chunk**:
  "Delhi University Official Circular 2026: All post-matric merit scholarship forms must reach the registrar desk by November 30, 2026."

- **Final Generated Answer**:
  "According to the official circular, the last date to submit your scholarship form is November 30, 2026."

Notice how the AI did not guess.
It read the exact circular chunk and gave the true date.

---

## 5. RAG vs Fine-Tuning: What is the Difference?

Many students confuse RAG with fine-tuning.
Let us make the difference clear.

Fine-tuning changes the internal neural weights of the AI model.
It is like studying for months before a hard closed-book test.
It changes how the model speaks or thinks.
However, fine-tuning is slow and costly.

RAG never changes or retrains the neural weights of the model.
The model weights remain completely frozen.
Instead, RAG simply hands notes to the model before it answers.
RAG is fast, cheap, and easy to update daily.

---

## 6. Real-World Limitations of RAG

RAG is very powerful, but it is not magic.
Every good engineer must know where it fails.

1. **Garbage In, Garbage Out**:
   If your external database has wrong facts, the answer will be wrong.
   The AI trusts the text you give it.
2. **Retrieval Misses**:
   If the search tool picks the wrong paragraph, the model cannot answer well.
3. **Extra Time**:
   Searching a database adds a small delay before the answer appears.

---

## 7. Quick Summary & Key Takeaways

- RAG stands for Retrieval-Augmented Generation.
- It acts like an open-book exam for AI models.
- It stops hallucinations by grounding answers in real documents.
- It uses chunking, embeddings, and a vector database.
- RAG does not retrain or alter model weights.

---

## 8. Self-Check Questions

Check your skills with these four quick practice questions.

1. **Question**: Does RAG retrain the weights of the AI model?
   **Answer**: No. RAG keeps model weights frozen and only provides external notes.

2. **Question**: What is chunking?
   **Answer**: Chunking means cutting large documents into smaller, readable paragraphs.

3. **Question**: What is hallucination in AI?
   **Answer**: Hallucination is when an AI invents believable but completely false facts.

4. **Question**: What real-life analogy describes RAG best?
   **Answer**: A student taking an open-book exam and looking up facts in a textbook.
"""

def get_flawed_mock_lesson(injected_error: Optional[str] = None) -> str:
    """Returns an attempt 1 mock draft with deliberate flaws to exercise the evaluation and reflection loop."""
    if injected_error == "factual":
        return """# Introduction to Retrieval-Augmented Generation (RAG)

In this lesson we study RAG.
RAG was invented in 2012 by IBM engineers in New York.
The main feature of RAG is that it retrains the model neural network weights every night.
Every time a user asks a query, RAG updates the internal parameters of the LLM.
This is different from normal searching.

## What is RAG?
RAG stands for Retrieval-Augmented Generation.
It modifies model weights directly using gradient descent on customer data.

## Why RAG Matters
RAG matters because models forget things.

## How RAG Works
1. Document ingest.
2. Weight retraining.
3. Output answer.

## Worked Example
- **Learner Question**: What is the deadline?
- **Retrieved Reference Chunk**: Circular: Deadline is Nov 30.
- **Final Generated Answer**: The deadline is Nov 30.

## Limitations
It takes a lot of GPU power to retrain weights.

## Summary
RAG retrains weights.

## Self-Check Questions
1. Does RAG retrain weights? Answer: Yes, it retrains weights continuously.
"""
    elif injected_error == "jargon":
        return """# Introduction to Retrieval-Augmented Generation (RAG)

We describe how high-dimensional ANN indexes optimize the parametric memory of transformers.
When deploying dense embeddings across multi-tenant vector DB clusters, engineers must calculate the cosine distance between query vectors and tokenized document chunks to avoid catastrophic retrieval degradation across arbitrary context boundaries.

## What is RAG?
RAG leverages external knowledge bases without parametric drift.
We utilize HNSW graphs and ANN approximations to retrieve top-k passages.

## Why RAG Matters
Standard architectures suffer from severe epistemic closure and bounded context windows.

## How RAG Works
The ingestion pipeline converts semi-structured corpus passages into dense vectors.

## Worked Example
- **Learner Question**: How does it work?
- **Retrieved Reference Chunk**: Vector embeddings match nearest neighbor.
- **Final Generated Answer**: It matches nearest neighbor.

## Limitations
Latent space collisions and index sharding bottlenecks.

## Summary
Dense vector retrieval.

## Self-Check Questions
1. What is ANN? Answer: Approximate nearest neighbor.
"""
    elif injected_error == "missing-example":
        lesson = get_passing_mock_lesson()
        # Remove Section 4 Worked Example entirely
        lesson = lesson.replace("## 4. Worked Example: Step-by-Step in Action", "## 4. Conceptual Architecture")
        lesson = lesson.replace("**Learner Question**:", "Concept Question:")
        lesson = lesson.replace("**Retrieved Reference Chunk**:", "Reference Data:")
        lesson = lesson.replace("**Final Generated Answer**:", "Output:")
        return lesson
    else:
        # Normal mock Attempt 1: Has one sentence > 25 words and an unexpanded acronym to trigger Layer A checks
        lesson = get_passing_mock_lesson()
        # Introduce a long sentence > 25 words (28 words) in section 2
        bad_sentence = "When an artificial intelligence tries to answer questions about brand new real-world events without having access to updated books, it will often invent false facts and confuse the reader completely."
        lesson = lesson.replace(
            "An AI model trained in 2023 knows nothing about events in 2026.",
            bad_sentence
        )
        # Introduce an unexpanded acronym "ANN"
        lesson = lesson.replace(
            "vector database (DB)",
            "vector database (DB) with ANN search"
        )
        return lesson

def get_mock_lesson(attempt: int = 1, injected_error: Optional[str] = None) -> str:
    """Mock generator dispatcher: Attempt 1 returns flawed text, Attempt 2+ returns passing text."""
    if attempt == 1:
        return get_flawed_mock_lesson(injected_error)
    return get_passing_mock_lesson()

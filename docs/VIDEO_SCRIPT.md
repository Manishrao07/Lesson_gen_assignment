# Loom Video Walkthrough Script (15–20 Minutes)

**Role:** GenAI Engineer – Content Systems  
**Project:** LessonGen Autonomous Lesson Generator & Evaluator  
**Format:** Face-visible recording with screen sharing (Loom)  
**Total Target Time:** 18:00 – 20:00 Minutes

---

## Visual & Setup Checklist Before Recording
- [ ] Webcam enabled in corner showing your face throughout the entire video.
- [ ] IDE open showing the `gen_ai` workspace.
- [ ] Terminal open and sized legibly with virtual environment activated (`source .venv/bin/activate`).
- [ ] Browser tabs ready:
  1. `docs/architecture.mmd` (or Mermaid preview).
  2. `outputs/final_lesson.md` and `outputs/final_lesson.docx`.
  3. Google AI Studio & Groq Console (showing free API key dashboards).

---

## Scene-by-Scene Script & Timeline

### Scene 1: Face-Visible Intro & Problem Context (00:00 – 02:00 | 2 Mins)
**What to show:** Full webcam or webcam + title slide (`README.md`).  
**What to say:**
> *"Hi everyone, my name is [Your Name], and this is my submission for the GenAI Engineer – Content Systems role. Today, I'm presenting **LessonGen**, an autonomous agentic system that generates beginner technical lessons, evaluates them against a strict rubric of hard binary pass/fail checkpoints, and regenerates content until it is truly good enough to ship before any human ever sees it.*
>
> *Everything in this project was built to run strictly on **100% free-tier APIs**—using Google Gemini for planning and generation, and Groq running Llama for independent evaluation, with zero paid subscriptions.*
>
> *Every single design choice was driven by our target learner: **a 12th-grade graduate from India with limited English vocabulary and non-English schooling**. They don't need academic papers or complex jargon. They need short sentences under 15 words, plain-English definitions at first use, and everyday Indian life analogies like open-book exams and chai-stall ledgers. Let's look at the architecture that makes this possible."*

---

### Scene 2: Architecture & LangGraph State Machine (02:00 – 06:00 | 4 Mins)
**What to show:** `README.md` or `docs/architecture.mmd` showing the Mermaid diagram, then `lessongen/graph.py`.  
**What to say:**
> *"Here is the architectural diagram of LessonGen. I chose **LangGraph** because content generation with validation and repair is fundamentally a cyclic state machine—not a linear chain.*
>
> *Let's trace the flow:*
> 1. *It begins by loading learned rules from memory.*
> 2. *The **Planner Node** reads our verified grounding pack (`knowledge/rag_facts.md`) and creates a structured lesson blueprint.*
> 3. *The **Generator Node** drafts the lesson using Gemini.*
> 4. *The draft enters our **Two-Layer Evaluator**: Layer A runs deterministic code checks, and Layer B runs our independent Groq/Llama judge.*
> 5. *The **Router** checks: if all 16 checkpoints pass, we route to the **Finalizer**.*
> 6. *If any checkpoint fails, the **Reflector Node** analyzes the failure evidence, formulates minimal surgical edit instructions, and loops back to the Generator.*
> 7. *Crucially, we enforce a strict invariant: **max 2 retries**. If attempt 3 still fails, the system does not crash or loop forever; it escalates to the Finalizer flagged as `NEEDS_HUMAN_REVIEW` with the full diagnostic rejection log.*
>
> *Let's inspect `lessongen/graph.py`—notice how cleanly the state transitions and conditional router edges are wired."*

---

### Scene 3: The Rubric & Two-Layer Evaluation Philosophy (06:00 – 09:00 | 3 Mins)
**What to show:** `rubric/rubric.yaml` and `lessongen/evaluator/layer_a.py`.  
**What to say:**
> *"Next, let's talk about the evaluation rubric in `rubric/rubric.yaml`. There are 16 hard binary checkpoints grouped across 6 dimensions: Accuracy, Beginner Language, Examples, Jargon Clarity, Coverage, and Flow.*
>
> *Why hard pass/fail instead of 1-to-5 scores? Because averages hide fatal errors! If a lesson gets 5/5 on grammar and tone, but states that 'RAG retrains model weights,' an average score of 90% would pass it. But for a beginner, that one falsehood ruins their mental model. A binary checkpoint means zero partial credit.*
>
> *Notice our two-layer split:*
> - *In `layer_a.py`, we use Python regex and `textstat` for deterministic metrics: average sentence length <= 15 words, zero sentences over 25 words, Flesch Reading Ease >= 65, and unexpanded acronym detection. LLMs are notoriously bad at counting words, so code handles the physical metrics.*
> - *In `layer_b.py`, we use Groq Llama at temperature 0 for semantic evaluation: consistency with the grounding pack, Indian analogies, and absence of idioms. By using Groq for the judge while Gemini generates, we completely eliminate **self-grading bias**."*

---

### Scene 4: Live End-to-End Pipeline Execution (09:00 – 12:00 | 3 Mins)
**What to show:** Terminal running `python -m lessongen run --mock`.  
**What to say:**
> *"Now let's see the system run end-to-end. I'll execute `python -m lessongen run --mock` in the terminal.*
>
> *(Run the command and observe the output)*
>
> *Look at the terminal: the LangGraph state machine starts at Attempt 1. In Attempt 1, the candidate draft is evaluated. Layer A detects a sentence exceeding 25 words and an unexpanded acronym. The Router catches the failure and dispatches to the Reflector.*
>
> *The Reflector analyzes the exact quotes and generates a targeted fix instruction. The Generator runs Attempt 2. On Attempt 2, all 16 checkpoints pass! The Router approves the lesson, and the Finalizer generates all output artifacts in `/outputs`:*
> - *Let's open `outputs/final_lesson.md`: clean, beautifully formatted markdown, open-book exam analogy, worked example with Question, Chunk, and Answer, and self-check practice questions.*
> - *And here is `outputs/final_lesson.docx`, styled and ready for sharing.*
> - *And `outputs/rejection_log.md`, documenting the exact history of what failed and how it was healed."*

---

### Scene 5: Deliberate Error Demonstration (12:00 – 15:00 | 3 Mins)
**What to show:** Terminal running `python -m lessongen run --mock --inject-error factual`, then show `outputs/demo_rejection_log.md`.  
**What to say:**
> *"A key requirement of this assessment is proving that the evaluator is real and catches deliberate errors.*
>
> *Let's run `python -m lessongen run --mock --inject-error factual`.*
>
> *(Run command)*
>
> *Here, we injected a factual falsehood into Attempt 1: claiming that 'RAG retrains the model neural network weights every night' and citing a fake 2012 IBM origin.*
>
> *Look at the evaluation table: Checkpoint `ACC-1` and `ACC-3` immediately failed with direct quote evidence: 'The main feature of RAG is that it retrains the model neural network weights every night.'*
>
> *The Reflector intervened, explicitly told the Generator that RAG keeps weights frozen, and on Attempt 2, the error was completely purged and the lesson passed.*
>
> *Let's inspect `outputs/demo_rejection_log.md`—it contains the full audit trail of the caught error, the diagnosis, the repair plan, and the passing retry."*

---

### Scene 6: Memory & Self-Evolution Demonstration (15:00 – 18:00 | 3 Mins)
**What to show:** `memory/runs.jsonl`, `memory/learned_rules.json`, run `python -m lessongen evolve`, and `outputs/memory_demo.md`.  
**What to say:**
> *"Now let's look at the self-evolving memory system. Every run is logged to `memory/runs.jsonl`.*
>
> *When a failure occurs, the system distills preventative rules into `memory/learned_rules.json`—for example: 'Hard limit: Never write any sentence longer than 25 words' and 'Always expand key acronyms on first mention'.*
>
> *Let's look at `outputs/memory_demo.md`. On Run #1, the system needed 2 attempts. On Run #2, having loaded these learned rules into the Planner and Generator, the lesson passed on the **very first attempt** with a 100% pass rate! That is a 50% reduction in API calls and token quota.*
>
> *Now, let's run our evolution engine: `python -m lessongen evolve --threshold 1.0`.*
>
> *(Run command)*
>
> *The Evolver aggregates failure telemetry, creates `prompts/generator_v2.txt`, and generates `rubric/rubric_v2.yaml`. Notice our **safety invariant**: the Evolver tightened the sentence ceiling from 25 to 22 words—it NEVER auto-loosens thresholds. And it requires human approval (`--approve`) before touching the active rubric."*

---

### Scene 7: Trade-offs & Wrap-up (18:00 – 20:00 | 2 Mins)
**What to show:** Full webcam.  
**What to say:**
> *"To wrap up, let's discuss trade-offs and future vision.*
>
> *First, **latency versus rigor**: running two models plus deterministic checkers adds about 5 seconds compared to a single prompt. For education, that extra 5 seconds is a non-negotiable price for correctness and student trust.*
>
> *Second, **strictness versus flexibility**: rejecting a lesson because one sentence is 26 words is strict. But for our 12th-grade learner from India, long sentences mean cognitive overload. The strict ceiling guarantees accessibility.*
>
> *If I were building this into production next, I would add a live ChromaDB retrieval layer over textbook archives, an automated 'Judge-the-Judge' benchmark test suite to monitor evaluator drift, and a web review studio for editorial teams.*
>
> *Thank you so much for your time and for reviewing LessonGen. I look forward to discussing the design and codebase in our interview!"*

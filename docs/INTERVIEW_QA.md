# Technical Interview Defense: Model Questions & Answers

**Role:** GenAI Engineer – Content Systems  
**Project:** LessonGen  
**Format:** Direct, high-signal answers to anticipated architectural questions.

---

### Q1: Why did you choose hard binary pass/fail checkpoints instead of numerical scores (e.g. 1–5 or 0–100%)?
**Answer:**  
*"In educational content systems, numerical averages hide fatal edge-case failures. If a lesson scores 5/5 on grammar, 5/5 on structure, and 4/5 on tone, an overall score of 93% would comfortably pass it in a scoring system. But if that same lesson states that 'RAG retrains model weights during query time,' it has taught a fundamental technical falsehood that damages the beginner's understanding.*

*A binary rubric removes partial credit: every checkpoint either strictly passes or fails. Furthermore, binary checks provide deterministic feedback. Telling an LLM 'your score was 3.5/5' is vague; telling it 'Checkpoint BEG-2 failed because this 28-word sentence exceeded the 25-word limit' gives the Reflector an exact, actionable target to repair."*

---

### Q2: What happens if the LLM judge hallucinates or passes a bad lesson (a false negative)? How is that mitigated?
**Answer:**  
*"We protect against judge false negatives through a three-layer defense:*
1. *Deterministic Layer A: Physical, measurable properties (sentence lengths, reading scores, section headings, and acronym expansions) are never delegated to the LLM judge. They are checked deterministically in Python code with zero hallucination risk.*
2. *Mandatory Quote Evidence: Layer B requires the judge to extract verbatim quotes from the candidate text proving that the pass condition was satisfied. If the judge cannot extract evidence, the checkpoint fails.*
3. *Cross-Model Auditing: The judge runs on an independent model family (Llama 3.3/3.1 via Groq) at temperature 0.0, completely separate from Gemini which generated the draft. This eliminates self-grading bias and sycophancy.*
4. *Human Review Escalation: If any edge case persists after 2 retries, the system never forces a pass—it flags the lesson as `NEEDS_HUMAN_REVIEW` with the full diagnostic rejection log."*

---

### Q3: How do you prevent "rubric drift" when the self-evolution engine updates rules?
**Answer:**  
*"Rubric drift occurs when autonomous systems quietly relax evaluation thresholds over time to make pass rates look artificially higher. In LessonGen, I enforced two architectural guardrails in `lessongen/evolver.py`:*
1. *Threshold Monotonicity Invariant: The Evolver is programmatically forbidden from loosening thresholds. It can only tighten ceilings (e.g. reducing max sentence length from 25 to 22 words) or introduce additional required checks—never relax them.*
2. *Human-in-the-Loop Promotion Gate: While prompt improvements (`prompts/generator_v2.txt`) can be generated automatically, changes to the active rubric require an explicit human `--approve` flag before `rubric_v2.yaml` is promoted to `rubric.yaml`."*

---

### Q4: Why did you bound retries to a maximum of 2? Why not allow 5 or 10 retries?
**Answer:**  
*"Three reasons: cost, latency, and diminishing returns.*
*First, on free-tier APIs, unconstrained retries burn through quota and trigger rate limits.*
*Second, empirical observation of LLMs shows that if an agent cannot resolve a defect within 2 retries with targeted reflection instructions, it is usually trapped in an oscillation loop (where fixing one sentence inadvertently violates another constraint).*
*Third, operational pragmatism: in an enterprise editorial pipeline, an automated agent should handle the 90% happy path. If a candidate draft fails 3 consecutive attempts, the correct engineering decision is to halt the loop and escalate the draft to a human editor with pre-compiled diagnostic logs."*

---

### Q5: How do you prove that Run #2 actually benefited from what Run #1 learned?
**Answer:**  
*"We demonstrate this quantitatively in `outputs/memory_demo.md`:*
- *In Run #1 (cold start, empty memory), the generator drafted a lesson that violated `BEG-2` (one 28-word sentence) and `JAR-2` (unexpanded 'ANN' acronym). It required a full retry cycle to heal.*
- *The failure was logged to `memory/runs.jsonl` and distilled into concrete constraints in `memory/learned_rules.json`.*
- *In Run #2 (warm start), the system injected those distilled rules into the initial Planner and Generator prompts. As a direct result, Run #2 achieved a **100% first-attempt pass rate**.*
- *This resulted in a 50% reduction in API calls and token consumption, directly proving that the agent learned from past mistakes."*

---

### Q6: How do you ensure the system runs 100% reliably on free-tier APIs without getting blocked by rate limits?
**Answer:**  
*"We implemented four free-tier safeguards in `lessongen/llm.py`:*
1. *SHA-256 Disk Caching: Prompt hashes are stored in `.cache/llm/`. Identical calls are served instantly from disk with zero network requests and zero quota burn.*
2. *Adaptive Exponential Backoff: We catch HTTP 429 and resource exhaustion errors, backing off exponentially (`2s -> 4s -> 8s`).*
3. *Inter-call Rate Throttling: A mandatory delay (`RATE_LIMIT_DELAY_SECONDS=2.0`) is enforced between live API requests.*
4. *Pydantic Auto-Repair: Malformed JSON from free models is caught locally and repaired with a single schema-guided retry prompt rather than restarting the entire pipeline.*
5. *Offline Mock Mode: Developers can test and rehearse every failure edge and state transition via `--mock` without consuming a single API credit."*

---

### Q7: If you were deploying this to production next week, what would you build next?
**Answer:**  
*"Three immediate priorities:*
1. *Dynamic Grounding Vector Store: Replace the static `knowledge/rag_facts.md` with an active vector database (Chroma/Qdrant) so the Planner can retrieve verified facts across an entire enterprise knowledge base.*
2. *Evaluator Benchmark Suite ('Judge-the-Judge'): A permanent gold test suite of 50 verified good lessons and 50 known-bad lessons run as part of CI/CD to measure the precision and recall of our Evaluator models before updating rubrics.*
3. *Human Editorial Studio: A lightweight web dashboard where human educators can review flagged lessons, inspect highlighted failure quotes, and click a button to promote evolved rules."*

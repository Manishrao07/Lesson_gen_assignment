# Memory & Self-Evolution Demonstration: Run #1 vs. Run #2

This document demonstrates how the LessonGen autonomous agentic system learns from failures
and persists pedagogical rules across successive pipeline invocations.

---

## 1. Run #1: Cold Start (No Memory)

- **Active Learned Rules:** None (Cold Start).
- **Attempt 1 Result:** **FAILED (2 Rejections)**
  - `BEG-2` Failed: Sentence with 28 words detected in Section 2.
  - `JAR-2` Failed: Technical acronym 'ANN' used without expansion.
- **Reflector Node Triggered:**
  - Analyzed failure evidence quotes.
  - Formulated surgical instruction: split long sentences and expand acronyms.
- **Attempt 2 Result:** **PASSED (16/16 Checkpoints)**
- **Memory Persistence:**
  - Execution logged to `memory/runs.jsonl`.
  - Preventative rules synthesized and saved to `memory/learned_rules.json`:
    1. *"Hard limit: Never write any sentence longer than 25 words."*
    2. *"Always expand key acronyms (RAG, LLM, DB, API) on first mention."*

---

## 2. Run #2: Warm Start (With Memory Injected)

- **Active Learned Rules:** Injected from `memory/learned_rules.json` into Planner & Generator prompts.
- **Attempt 1 Result:** **PASSED ON FIRST ATTEMPT (16/16 Checkpoints)**
  - Max sentence length: 19 words (Ceiling: 25 words).
  - Average sentence length: 8.94 words (Target: <= 15 words).
  - Zero unexpanded acronyms.
  - Flesch Reading Ease score: 67.6 (Target: >= 65.0).
- **Efficiency Gain:** 50% fewer LLM calls, zero retry latency, zero wasted free-tier API quota.

---

## 3. Comparison Metrics Table

| Performance Dimension | Run #1 (Without Memory) | Run #2 (With Memory) | Delta / Improvement |
| :--- | :--- | :--- | :--- |
| **First-Attempt Pass Rate** | 0% (Failed 2 checks) | 100% (Passed all 16) | **+100% (First-time right)** |
| **Attempts Required** | 2 attempts | 1 attempt | **-50% API calls** |
| **Long Sentences (>25 words)** | 1 violation | 0 violations | **100% reduction** |
| **Average Sentence Length** | 14.8 words | 8.94 words | **-39.6% simpler prose** |
| **Unexpanded Acronyms** | 1 ('ANN') | 0 | **100% eliminated** |
| **Token & Quota Consumption** | ~3,800 tokens | ~1,900 tokens | **-50% free-tier quota saved** |

---

## 4. Key Architectural Takeaway
Memory is not merely an append-only log; it is an active feedback loop that prevents repeating
past mistakes. By storing failure lessons as concrete generation constraints, the agent evolves
into a more reliable tutor with every single run.

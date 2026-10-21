# Take-Home Submission Checklist

**Role:** GenAI Engineer – Content Systems  
**Candidate Submission Verification Document**

---

## 1. Primary Submission Deliverables

- [ ] **GitHub Repository Link:**  
  *Repository URL:* `https://github.com/<your-username>/gen_ai_lesson_system`  
  *(Verify repository is set to Public or shared with the reviewing team)*

- [ ] **Final Lesson Document (Google Doc):**  
  *Google Doc URL:* `https://docs.google.com/document/d/<your-doc-id>/edit?usp=sharing`  
  *(Created by importing or pasting `outputs/final_lesson.md` or `outputs/final_lesson.docx`. Ensure sharing settings are "Anyone with the link can view")*

- [ ] **Loom Video Walkthrough (15–20 Minutes):**  
  *Loom Video URL:* `https://www.loom.com/share/<your-loom-video-id>`  
  *(Recorded following `docs/VIDEO_SCRIPT.md` with face visible throughout)*

---

## 2. Technical Requirements Verification

- [x] **Target Learner Alignment:**
  - [x] Average sentence length <= 15 words (`BEG-1`)
  - [x] Zero sentences > 25 words (`BEG-2`)
  - [x] Flesch Reading Ease score >= 65.0 (`BEG-3`)
  - [x] Every technical term defined in plain English at first use (`JAR-1`)
  - [x] Relatable Indian life analogies included (open-book exam, librarian) (`EX-1`)
  - [x] Complete 3-step worked example included (Question -> Retrieved Chunk -> Answer) (`EX-2`)
  - [x] Zero unexplained acronyms (`JAR-2`)
  - [x] Limitations and self-check questions with answers included (`COV-3`, `FLOW-2`)

- [x] **Agentic & Free-Tier Architecture:**
  - [x] LangGraph state machine with cyclic retry loop
  - [x] Provider-agnostic LLM caller (`lessongen/llm.py`) supporting Google Gemini, Groq, Ollama, and Mock
  - [x] Cross-architecture judge (Gemini generator + Groq/Llama judge) eliminating self-grading bias
  - [x] Zero API keys hardcoded; `.env` listed in `.gitignore` with `.env.example` provided
  - [x] Free-tier safeguards: SHA-256 disk caching, exponential backoff, rate-limit throttling, JSON auto-repair
  - [x] Complete `--mock` mode exercising failure-then-pass path without API keys

- [x] **Hard Binary Evaluation & Bounded Retries:**
  - [x] 16 hard binary checkpoints in `rubric/rubric.yaml`
  - [x] Two-layer evaluation (Layer A code checks + Layer B LLM judge)
  - [x] Bounded to max 2 retries (loop always terminates)
  - [x] Graceful escalation to `NEEDS_HUMAN_REVIEW` on persistent failure
  - [x] Rejection log outputs (`outputs/rejection_log.md` and `.json`)

- [x] **Memory & Self-Evolution:**
  - [x] Run logging to `memory/runs.jsonl`
  - [x] Distilled rules in `memory/learned_rules.json` injected into future runs
  - [x] Memory demo report (`outputs/memory_demo.md`) proving Run #2 improved over Run #1
  - [x] Evolution engine (`lessongen evolve`) synthesizing `prompts/generator_v2.txt`, `rubric/rubric_v2.yaml`, and `CHANGELOG.md`
  - [x] Rubric threshold monotonicity enforced (never auto-loosened; `--approve` flag required)
  - [x] Human feedback CLI (`lessongen feedback --run <id> --text "..."`)

- [x] **Deliberate Error Demo:**
  - [x] `--inject-error factual|jargon|missing-example` flag implemented
  - [x] Evaluator catches error with exact quote evidence on Attempt 1
  - [x] Reflector guides Generator to heal error on Attempt 2
  - [x] Demo report written to `outputs/demo_rejection_log.md`

- [x] **Comprehensive Documentation:**
  - [x] `README.md` (Setup, CLI commands, Mermaid diagram, outputs overview)
  - [x] `DESIGN.md` (First-person architectural rationale, trade-offs, roadmap)
  - [x] `PLAN.md` (Initial implementation plan)
  - [x] `docs/architecture.mmd` (Mermaid diagram source)
  - [x] `docs/VIDEO_SCRIPT.md` (15-20 min Loom script with timestamps)
  - [x] `docs/INTERVIEW_QA.md` (Interview defense Q&A)
  - [x] Full automated test suite passing (`pytest`)

# Deliberate Error Demonstration Log

**Demonstration Scenario:** Injected `factual` error into candidate lesson.
**Objective:** Verify that Evaluator Layer catches the seeded error, cites direct quote evidence, and Reflector heals the draft on retry.

---

## Attempt 1 — Verdict: FAILED (Seeded Error Caught)

### Caught Checkpoints (8):

#### Checkpoint `BEG-3`
- **Evaluator Diagnosis**: Text is too dense/academic.
- **Direct Evidence Caught**: *"Flesch Reading Ease score: 57.0 (required >= 65.0)."*

#### Checkpoint `JAR-2`
- **Evaluator Diagnosis**: Acronyms must be expanded into plain words on first use.
- **Direct Evidence Caught**: *"Unexpanded acronyms found: LLM"*

#### Checkpoint `ACC-1`
- **Evaluator Diagnosis**: Direct contradiction of grounding pack: RAG was invented in 2020 by Patrick Lewis et al.
- **Direct Evidence Caught**: *"RAG was invented in 2012 by IBM engineers in New York."*

#### Checkpoint `ACC-3`
- **Evaluator Diagnosis**: Fails pass condition: RAG does NOT retrain or alter model weights; weights remain frozen.
- **Direct Evidence Caught**: *"The main feature of RAG is that it retrains the model neural network weights every night."*

#### Checkpoint `EX-1`
- **Evaluator Diagnosis**: Must include at least one relatable Indian life analogy.
- **Direct Evidence Caught**: *"No everyday analogy found."*

#### Checkpoint `COV-2`
- **Evaluator Diagnosis**: Blueprint mandatory concepts missing from lesson body.
- **Direct Evidence Caught**: *"Missing concepts: cutoff, vector"*

#### Checkpoint `COV-3`
- **Evaluator Diagnosis**: Must cover real-world failure modes and system limitations.
- **Direct Evidence Caught**: *"No limitations section found."*

#### Checkpoint `FLOW-1`
- **Evaluator Diagnosis**: Lacks structured beginner narrative arc.
- **Direct Evidence Caught**: *"Disjointed section progression."*

### Reflector Action Plan:
```text
Rubric Fix for BEG-3: Address pass condition: Text is too dense/academic.
Acronym Fix: Unexpanded acronyms were detected. Expand every acronym upon its first mention (e.g. 'Approximate Nearest Neighbor (ANN)').
Factual Accuracy Fix: Correct claims about model weights. RAG does NOT retrain or alter model weights; weights remain frozen. Also ensure Lewis et al. 2020 origin is accurately cited.
Factual Accuracy Fix: Correct claims about model weights. RAG does NOT retrain or alter model weights; weights remain frozen. Also ensure Lewis et al. 2020 origin is accurately cited.
Rubric Fix for EX-1: Address pass condition: Must include at least one relatable Indian life analogy.
Rubric Fix for COV-2: Address pass condition: Blueprint mandatory concepts missing from lesson body.
Rubric Fix for COV-3: Address pass condition: Must cover real-world failure modes and system limitations.
Worked Example Fix: Insert a complete worked example formatted strictly with: Learner Question -> Retrieved Reference Chunk -> Final Generated Answer.
```

**Diff Summary:** Addressed checkpoints BEG-3, JAR-2, ACC-1, ACC-3, EX-1, COV-2, COV-3, FLOW-1: Fixed BEG-3 issue.; Expanded unexpanded acronyms.; Corrected factual error regarding model weight retraining and paper origin.; Corrected factual error regarding model weight retraining and paper origin.; Fixed EX-1 issue.; Fixed COV-2 issue.; Fixed COV-3 issue.; Added complete 3-step worked example.

---

## Attempt 2 — Verdict: PASSED (Error Fixed)

> **Recovery Confirmed:** The candidate lesson was regenerated, removing all seeded errors. All 16 checkpoints passed.

---


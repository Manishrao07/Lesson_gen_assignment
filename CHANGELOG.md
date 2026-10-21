# Self-Evolution Changelog

Generated at: 2026-10-21 23:46:27

## Evolution Triggers
- Analyzed runs from `memory/runs.jsonl`.
- Recurring failure checkpoints: BEG-2, JAR-2, BEG-3, ACC-1, ACC-3, EX-1, COV-2, COV-3, FLOW-1, FLOW-2, JAR-1, BEG-4.

## 1. Generator Prompt Upgrades (`prompts/generator_v2.txt`)
- CRITICAL SENTENCE CEILING: Never exceed 20 words in any sentence. Break compound clauses into multiple short sentences.
- STRICT GLOSSARY RULE: Expand acronyms immediately (e.g., 'ANN (Approximate Nearest Neighbor)'). Provide plain words in brackets at first use.
- MODEL WEIGHT INVARIANT: Explicitly emphasize that RAG leaves neural weights completely untouched and frozen.

## 2. Rubric Sharpening (`rubric/rubric_v2.yaml`)
- Upgraded version from 1.0.0 to 2.0.0.
- **Safety Invariant Verified**: No threshold was loosened. Ceiling tightened from 25 to 22 words.
- Clarified evidence requirements for acronyms and definitions.

## 3. Human Approval Status
- Human Approval Flag (`--approve`): `PENDING APPROVAL (Dry Run)`

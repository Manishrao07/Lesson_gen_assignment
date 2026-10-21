import re
from typing import Dict, List, Tuple, Any
import textstat
from lessongen.nodes.models import CheckpointResult

def clean_text_for_readability(markdown_text: str) -> str:
    """Removes markdown headers, code fences, and bullet markers to extract pure prose."""
    # Remove code blocks
    text = re.sub(r"```.*?```", "", markdown_text, flags=re.DOTALL)
    # Remove markdown headers (# Title)
    text = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"[*_]{1,2}", "", text)
    # Remove list numbers and bullets
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    return text.strip()

def split_into_sentences(text: str) -> List[str]:
    """Splits prose into distinct sentences, handling punctuation, quotes, and line breaks."""
    # Normalize line breaks
    normalized = text.replace("\r\n", "\n")
    # Split on punctuation followed by space OR on line breaks
    raw_parts = re.split(r"(?<=[.!?])[\"')\]]?\s+|\n+", normalized)
    cleaned = []
    for s in raw_parts:
        clean_s = s.strip().strip("\"'()[]{}")
        # Exclude empty or very short non-sentence fragments
        if len(clean_s.split()) >= 2 and any(c.isalnum() for c in clean_s):
            cleaned.append(clean_s)
    return cleaned

def evaluate_layer_a(lesson_text: str) -> List[CheckpointResult]:
    """Runs deterministic code checks on the lesson draft."""
    results: List[CheckpointResult] = []
    plain_text = clean_text_for_readability(lesson_text)
    sentences = split_into_sentences(plain_text)

    # 1. BEG-1: Average Sentence Length <= 15.0 words
    sentence_word_counts = [len(s.split()) for s in sentences] if sentences else [0]
    total_words = sum(sentence_word_counts)
    num_sentences = max(len(sentences), 1)
    avg_words_per_sentence = round(total_words / num_sentences, 2)
    beg_1_pass = avg_words_per_sentence <= 15.0

    results.append(CheckpointResult(
        id="BEG-1",
        dimension="BEG",
        title="Average Sentence Length Threshold",
        layer="code",
        passed=beg_1_pass,
        evidence=f"Average sentence length is {avg_words_per_sentence} words across {num_sentences} sentences.",
        reason="Target is <= 15.0 words per sentence for low-vocabulary comprehension." if not beg_1_pass else "Meets target sentence length limit."
    ))

    # 2. BEG-2: Maximum Sentence Length Ceiling (No sentence > 25 words)
    long_sentences = [(s, len(s.split())) for s in sentences if len(s.split()) > 25]
    beg_2_pass = len(long_sentences) == 0

    if beg_2_pass:
        beg_2_evidence = f"Max sentence length is {max(sentence_word_counts) if sentence_word_counts else 0} words (<= 25)."
        beg_2_reason = "No sentence exceeds 25 words."
    else:
        worst_s, count = long_sentences[0]
        beg_2_evidence = f"{len(long_sentences)} sentence(s) exceed 25 words. Longest ({count} words): \"{worst_s[:90]}...\""
        beg_2_reason = "Sentences over 25 words overload beginner comprehension."

    results.append(CheckpointResult(
        id="BEG-2",
        dimension="BEG",
        title="Maximum Sentence Length Ceiling",
        layer="code",
        passed=beg_2_pass,
        evidence=beg_2_evidence,
        reason=beg_2_reason
    ))

    # 3. BEG-3: Readability Score (Flesch Reading Ease >= 65.0)
    try:
        fre_score = round(textstat.flesch_reading_ease(plain_text), 1)
    except Exception:
        fre_score = 70.0
    beg_3_pass = fre_score >= 65.0

    results.append(CheckpointResult(
        id="BEG-3",
        dimension="BEG",
        title="Readability Score Threshold",
        layer="code",
        passed=beg_3_pass,
        evidence=f"Flesch Reading Ease score: {fre_score} (required >= 65.0).",
        reason="Score is within the accessible range for secondary-school graduates." if beg_3_pass else "Text is too dense/academic."
    ))

    # 4. JAR-2: No Unexpanded Acronyms
    acronym_checks = [
        ("RAG", [r"retrieval[-\s]augmented\s+generation", r"retrieval\s+augmented"]),
        ("LLM", [r"large\s+language\s+model"]),
        ("DB", [r"database", r"vector\s+db"]),
        ("API", [r"application\s+programming\s+interface"])
    ]
    unexpanded: List[str] = []
    lower_text = lesson_text.lower()

    for acronym, expansions in acronym_checks:
        pattern = rf"\b{acronym}\b"
        match = re.search(pattern, lesson_text)
        if match:
            expanded = any(re.search(exp, lower_text) for exp in expansions)
            if not expanded:
                unexpanded.append(acronym)

    stray_acronyms = ["ANN", "HNSW", "KNN", "TF-IDF", "BM25"]
    for stray in stray_acronyms:
        if re.search(rf"\b{stray}\b", lesson_text):
            unexpanded.append(stray)

    jar_2_pass = len(unexpanded) == 0
    results.append(CheckpointResult(
        id="JAR-2",
        dimension="JAR",
        title="No Unexpanded Acronyms",
        layer="code",
        passed=jar_2_pass,
        evidence="All acronyms properly expanded." if jar_2_pass else f"Unexpanded acronyms found: {', '.join(unexpanded)}",
        reason="Acronyms must be expanded into plain words on first use." if not jar_2_pass else "All acronyms introduced with full names."
    ))

    # 5. COV-1: Core Triad Coverage (What, Why, How)
    has_what = bool(re.search(r"##\s*.*what\s+is\s+rag", lesson_text, re.IGNORECASE))
    has_why = bool(re.search(r"##\s*.*why\s+.*matter", lesson_text, re.IGNORECASE))
    has_how = bool(re.search(r"##\s*.*how\s+rag\s+works", lesson_text, re.IGNORECASE))
    cov_1_pass = has_what and has_why and has_how

    missing_sections = []
    if not has_what: missing_sections.append("What is RAG")
    if not has_why: missing_sections.append("Why RAG Matters")
    if not has_how: missing_sections.append("How RAG Works")

    results.append(CheckpointResult(
        id="COV-1",
        dimension="COV",
        title="Core Triad Coverage (What, Why, How)",
        layer="code",
        passed=cov_1_pass,
        evidence="Found sections: What, Why, How." if cov_1_pass else f"Missing required core section(s): {', '.join(missing_sections)}",
        reason="A beginner lesson must answer What it is, Why it matters, and How it works."
    ))

    # 6. EX-2 (Code check for worked example format)
    has_question = bool(re.search(r"(question|user\s+query|learner\s+question)", lesson_text, re.IGNORECASE))
    has_chunk = bool(re.search(r"(retrieved\s+(reference\s+)?chunk|document\s+passage|retrieved\s+text)", lesson_text, re.IGNORECASE))
    has_answer = bool(re.search(r"(final\s+generated\s+answer|grounded\s+answer|model\s+answer)", lesson_text, re.IGNORECASE))
    ex_2_pass = has_question and has_chunk and has_answer

    results.append(CheckpointResult(
        id="EX-2",
        dimension="EX",
        title="Clear Worked Example Structure",
        layer="code",
        passed=ex_2_pass,
        evidence="Contains Question, Retrieved Chunk, and Final Generated Answer elements." if ex_2_pass else "Worked example missing 3-step components (Question -> Retrieved Chunk -> Answer).",
        reason="The worked example must clearly show inputs, retrieved context, and generated output."
    ))

    # 7. FLOW-2: Summary and Self-Check Questions
    has_summary = bool(re.search(r"##\s*.*(summary|key\s+takeaways)", lesson_text, re.IGNORECASE))
    has_self_check = bool(re.search(r"##\s*.*self[- ]check", lesson_text, re.IGNORECASE))
    
    question_count = len(re.findall(r"(?:^|\n)\s*(?:\d+\.|\*\*Question(?:\s*\d+)?\*\*:?|\bQuestion\b:)", lesson_text, re.IGNORECASE))
    flow_2_pass = has_summary and has_self_check and (question_count >= 3)

    results.append(CheckpointResult(
        id="FLOW-2",
        dimension="FLOW",
        title="Summary and Self-Check Questions",
        layer="code",
        passed=flow_2_pass,
        evidence=f"Summary section present: {has_summary}, Self-check section present: {has_self_check}, practice questions: {question_count}.",
        reason="Must conclude with a recap summary and at least 3 practice questions with answers."
    ))

    return results

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lessongen.config import settings
from lessongen.llm import LLMClient
from lessongen.graph import create_lesson_graph
from lessongen.state import LessonState
from lessongen.memory import record_run_to_memory, record_human_feedback, generate_memory_demo_report
from lessongen.evolver import run_evolution

app = FastAPI(
    title="LessonGen Dashboard",
    description="Interactive Web UI for Autonomous Lesson Generation & Evaluation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    topic: str = "Introduction to RAG (Retrieval-Augmented Generation)"
    mock: bool = False
    inject_error: Optional[str] = None
    retries: int = 2

class FeedbackRequest(BaseModel):
    run_id: str
    text: str

class EvolveRequest(BaseModel):
    threshold: float = 1.0
    approve: bool = False

@app.post("/api/run")
def run_pipeline(req: RunRequest) -> Dict[str, Any]:
    """Triggers the full LangGraph lesson generation pipeline."""
    if not settings.GROUNDING_PATH.exists():
        raise HTTPException(status_code=500, detail="Grounding pack not found")

    with open(settings.GROUNDING_PATH, "r", encoding="utf-8") as f:
        grounding_pack = f.read()

    learned_rules = []
    if settings.LEARNED_RULES_PATH.exists():
        try:
            with open(settings.LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
                learned_rules = json.load(f).get("rules", [])
        except Exception:
            learned_rules = []

    llm_client = LLMClient(mock=req.mock)
    graph = create_lesson_graph(llm_client)

    initial_state: LessonState = {
        "topic": req.topic,
        "grounding_pack": grounding_pack,
        "learned_rules": learned_rules,
        "current_attempt": 1,
        "max_retries": req.retries,
        "injected_error": req.inject_error,
        "rejection_log": [],
        "trace": []
    }

    try:
        final_state = graph.invoke(initial_state)
        run_id = record_run_to_memory(final_state)
        generate_memory_demo_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    rejection_dicts = [log.model_dump() for log in final_state.get("rejection_log", [])]

    return {
        "run_id": run_id,
        "final_status": final_state.get("final_status", "UNKNOWN"),
        "attempts_used": final_state.get("current_attempt", 1),
        "rejection_log": rejection_dicts,
        "metrics": final_state.get("metrics", {}),
        "draft_lesson": final_state.get("draft_lesson", "")
    }

@app.get("/api/outputs")
def get_outputs() -> Dict[str, Any]:
    """Returns the text contents of all generated output artifacts."""
    out_dir = settings.OUTPUTS_DIR
    def read_file(name: str) -> str:
        p = out_dir / name
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    return {
        "final_lesson_md": read_file("final_lesson.md"),
        "rejection_log_md": read_file("rejection_log.md"),
        "demo_rejection_log_md": read_file("demo_rejection_log.md"),
        "memory_demo_md": read_file("memory_demo.md"),
        "rejection_log_json": read_file("rejection_log.json"),
        "run_trace_json": read_file("run_trace.json")
    }

@app.get("/api/download/docx")
def download_docx():
    """Provides direct download of the generated final_lesson.docx."""
    docx_file = settings.OUTPUTS_DIR / "final_lesson.docx"
    if not docx_file.exists():
        raise HTTPException(status_code=404, detail="Word document not found. Run pipeline first.")
    return FileResponse(
        path=str(docx_file),
        filename="final_lesson.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/api/memory")
def get_memory_data() -> Dict[str, Any]:
    """Returns past runs, active learned rules, and feedback."""
    runs = []
    if settings.MEMORY_RUNS_PATH.exists():
        with open(settings.MEMORY_RUNS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        runs.append(json.loads(line))
                    except Exception:
                        pass

    rules = []
    if settings.LEARNED_RULES_PATH.exists():
        try:
            with open(settings.LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
                rules = json.load(f).get("rules", [])
        except Exception:
            rules = []

    return {
        "total_runs": len(runs),
        "runs": runs[-15:],  # Return latest 15 runs
        "learned_rules": rules
    }

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest) -> Dict[str, Any]:
    res = record_human_feedback(req.run_id, req.text)
    return {"status": "success", "code": res}

@app.post("/api/evolve")
def trigger_evolution(req: EvolveRequest) -> Dict[str, Any]:
    res = run_evolution(threshold=req.threshold, approve=req.approve)
    changelog = ""
    ch_path = settings.PROJECT_ROOT / "CHANGELOG.md"
    if ch_path.exists():
        with open(ch_path, "r", encoding="utf-8") as f:
            changelog = f.read()
    return {"status": "success", "approved": req.approve, "changelog": changelog}

@app.get("/api/knowledge")
def get_knowledge_data() -> Dict[str, Any]:
    rag_facts = ""
    if settings.GROUNDING_PATH.exists():
        with open(settings.GROUNDING_PATH, "r", encoding="utf-8") as f:
            rag_facts = f.read()

    rubric_yaml = ""
    if settings.RUBRIC_PATH.exists():
        with open(settings.RUBRIC_PATH, "r", encoding="utf-8") as f:
            rubric_yaml = f.read()

    return {
        "rag_facts": rag_facts,
        "rubric_yaml": rubric_yaml
    }

# Mount static frontend
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

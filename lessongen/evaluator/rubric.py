from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field
from lessongen.config import settings

class RubricCheckpoint(BaseModel):
    id: str
    dimension: str
    layer: str  # "code" or "judge"
    title: str
    pass_condition: str
    rationale: str
    threshold: Optional[float] = None

class Rubric(BaseModel):
    version: str
    title: str
    description: str
    checkpoints: List[RubricCheckpoint]

def load_rubric(rubric_path: Optional[Path] = None) -> Rubric:
    path = rubric_path or settings.RUBRIC_PATH
    if not path.exists():
        raise FileNotFoundError(f"Rubric file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Rubric.model_validate(data)

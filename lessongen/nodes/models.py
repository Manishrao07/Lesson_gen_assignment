from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LessonBlueprint(BaseModel):
    learning_objectives: List[str] = Field(description="3-4 beginner learning objectives")
    key_concepts: List[str] = Field(description="Core technical concepts that must be covered")
    required_analogies: List[str] = Field(description="Everyday Indian life analogies")
    worked_example_plan: Dict[str, str] = Field(description="Plan for the 3-step worked example")
    sections: List[str] = Field(description="Ordered list of section titles")

class CheckpointResult(BaseModel):
    id: str = Field(description="Checkpoint ID e.g. ACC-1, BEG-1")
    dimension: str = Field(description="Dimension name (ACC, BEG, EX, JAR, COV, FLOW)")
    title: str = Field(description="Human readable title")
    layer: str = Field(description="'code' or 'judge'")
    passed: bool = Field(description="True if checkpoint passed, False if failed")
    evidence: str = Field(description="Quote from text or metric value")
    reason: str = Field(description="Explanation for pass or fail verdict")

class JudgeItem(BaseModel):
    id: str = Field(description="Checkpoint ID e.g. ACC-1")
    passed: bool = Field(description="True if checkpoint passed, False if failed")
    evidence: str = Field(default="", description="Short quote or evidence under 15 words")
    reason: str = Field(default="", description="Concise explanation under 15 words")

class EvaluatorJudgment(BaseModel):
    checkpoints: List[JudgeItem] = Field(description="List of checkpoint evaluations")

class AttemptLog(BaseModel):
    attempt: int
    passed: bool
    failed_checkpoints: List[str]
    reasons: Dict[str, str]
    evidence: Dict[str, str]
    fix_instruction: Optional[str] = None
    diff_summary: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

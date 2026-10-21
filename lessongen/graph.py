import logging
import time
from typing import Any, Dict, List, Literal, Optional
from langgraph.graph import StateGraph, START, END
from lessongen.config import settings
from lessongen.llm import LLMClient
from lessongen.state import LessonState
from lessongen.nodes.models import AttemptLog
from lessongen.nodes.planner import plan_lesson
from lessongen.nodes.generator import generate_lesson
from lessongen.evaluator import evaluate_lesson
from lessongen.nodes.reflector import reflect_on_failures
from lessongen.nodes.finalizer import finalize_lesson_outputs

logger = logging.getLogger("lessongen.graph")

def create_lesson_graph(llm_client: LLMClient):
    """Builds and compiles the complete LangGraph state machine with 2-layer evaluation and reflection."""

    def planner_node(state: LessonState) -> Dict[str, Any]:
        logger.info(f"--- [Node 1: Planner] Building blueprint for topic: '{state['topic']}' ---")
        blueprint = plan_lesson(
            topic=state["topic"],
            grounding_pack=state.get("grounding_pack", ""),
            learned_rules=state.get("learned_rules", []),
            llm_client=llm_client
        )
        trace_entry = {
            "node": "planner",
            "timestamp": time.time(),
            "output": {"learning_objectives": blueprint.learning_objectives}
        }
        trace = list(state.get("trace", []))
        trace.append(trace_entry)
        return {
            "blueprint": blueprint,
            "current_attempt": 1,
            "rejection_log": [],
            "trace": trace
        }

    def generator_node(state: LessonState) -> Dict[str, Any]:
        attempt = state.get("current_attempt", 1)
        logger.info(f"--- [Node 2: Generator] Drafting lesson (Attempt {attempt}) ---")
        draft = generate_lesson(
            blueprint=state["blueprint"],
            grounding_pack=state.get("grounding_pack", ""),
            learned_rules=state.get("learned_rules", []),
            llm_client=llm_client,
            attempt=attempt,
            retry_instructions=state.get("retry_instructions"),
            injected_error=state.get("injected_error")
        )
        trace_entry = {
            "node": "generator",
            "attempt": attempt,
            "timestamp": time.time(),
            "draft_preview": draft[:200]
        }
        trace = list(state.get("trace", []))
        trace.append(trace_entry)
        return {
            "draft_lesson": draft,
            "trace": trace
        }

    def evaluator_node(state: LessonState) -> Dict[str, Any]:
        attempt = state.get("current_attempt", 1)
        logger.info(f"--- [Node 3: Evaluator] Running Layer A & B checks (Attempt {attempt}) ---")
        
        report = evaluate_lesson(
            lesson_text=state["draft_lesson"],
            grounding_pack=state.get("grounding_pack", ""),
            llm_client=llm_client,
            injected_error=state.get("injected_error") if attempt == 1 else None
        )

        failed_checkpoints = report.failed_checkpoints
        reasons_map = {cp.id: cp.reason for cp in failed_checkpoints}
        evidence_map = {cp.id: cp.evidence for cp in failed_checkpoints}

        attempt_log = AttemptLog(
            attempt=attempt,
            passed=report.overall_passed,
            failed_checkpoints=[cp.id for cp in failed_checkpoints],
            reasons=reasons_map,
            evidence=evidence_map,
            fix_instruction=state.get("retry_instructions"),
            metrics=report.metrics
        )

        rejection_log = list(state.get("rejection_log", []))
        rejection_log.append(attempt_log)

        trace_entry = {
            "node": "evaluator",
            "attempt": attempt,
            "passed": report.overall_passed,
            "failed_count": len(failed_checkpoints),
            "timestamp": time.time()
        }
        trace = list(state.get("trace", []))
        trace.append(trace_entry)

        return {
            "overall_passed": report.overall_passed,
            "layer_a_results": report.layer_a_results,
            "layer_b_results": report.layer_b_results,
            "all_checkpoints": report.checkpoints,
            "rejection_log": rejection_log,
            "metrics": report.metrics,
            "trace": trace
        }

    def reflector_node(state: LessonState) -> Dict[str, Any]:
        attempt = state.get("current_attempt", 1)
        logger.info(f"--- [Node 4: Reflector] Analyzing Attempt {attempt} failures for retry ---")
        
        current_log = state["rejection_log"][-1]
        failed_cps = [cp for cp in state.get("all_checkpoints", []) if not cp.passed]

        fix_instruction, diff_summary = reflect_on_failures(
            failed_checkpoints=failed_cps,
            draft_lesson=state["draft_lesson"],
            llm_client=llm_client
        )

        # Update latest attempt log with reflector outputs
        rejection_log = list(state.get("rejection_log", []))
        if rejection_log:
            rejection_log[-1].fix_instruction = fix_instruction
            rejection_log[-1].diff_summary = diff_summary

        trace_entry = {
            "node": "reflector",
            "attempt": attempt,
            "diff_summary": diff_summary,
            "timestamp": time.time()
        }
        trace = list(state.get("trace", []))
        trace.append(trace_entry)

        return {
            "current_attempt": attempt + 1,
            "retry_instructions": fix_instruction,
            "rejection_log": rejection_log,
            "trace": trace
        }

    def finalizer_node(state: LessonState) -> Dict[str, Any]:
        logger.info("--- [Node 5: Finalizer] Writing outputs and persisting artifacts ---")
        final_status = "PASSED" if state.get("overall_passed") else "NEEDS_HUMAN_REVIEW"
        state["final_status"] = final_status
        outputs = finalize_lesson_outputs(state)
        
        trace_entry = {
            "node": "finalizer",
            "final_status": final_status,
            "timestamp": time.time(),
            "outputs": outputs
        }
        trace = list(state.get("trace", []))
        trace.append(trace_entry)
        return {
            "final_status": final_status,
            "trace": trace
        }

    def router_condition(state: LessonState) -> Literal["finalizer", "reflector"]:
        """Decides whether to pass to finalizer or retry through reflector."""
        if state.get("overall_passed", False):
            logger.info("Router decision: All checkpoints PASSED -> Finalizer")
            return "finalizer"

        current_attempt = state.get("current_attempt", 1)
        max_retries = state.get("max_retries", settings.MAX_RETRIES)
        # Note: with max_retries = 2, we allow attempt 1 (initial), attempt 2 (retry 1), attempt 3 (retry 2)
        # So we can retry if current_attempt <= max_retries
        if current_attempt <= max_retries:
            logger.info(f"Router decision: FAIL on attempt {current_attempt} <= max_retries {max_retries} -> Reflector")
            return "reflector"

        logger.warning(f"Router decision: Max retries ({max_retries}) exhausted -> Finalizer (NEEDS HUMAN REVIEW)")
        return "finalizer"

    # Assemble Graph
    builder = StateGraph(LessonState)
    builder.add_node("planner", planner_node)
    builder.add_node("generator", generator_node)
    builder.add_node("evaluator", evaluator_node)
    builder.add_node("reflector", reflector_node)
    builder.add_node("finalizer", finalizer_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "generator")
    builder.add_edge("generator", "evaluator")
    builder.add_conditional_edges(
        "evaluator",
        router_condition,
        {
            "finalizer": "finalizer",
            "reflector": "reflector"
        }
    )
    builder.add_edge("reflector", "generator")
    builder.add_edge("finalizer", END)

    return builder.compile()

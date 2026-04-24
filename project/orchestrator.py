"""Central orchestrator: drives agents, owns shared state, retries, validation."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional

from agents.guide_writer import run as guide_writer_agent
from agents.judge_agent import run as judge_agent
from agents.plan_builder import run as plan_builder_agent
from agents.policy_fetcher import run as policy_fetcher_agent
from agents.role_researcher import run as role_researcher_agent

RETRY_BACKOFF_BASE_S = 0.35


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def initial_state() -> Dict[str, Any]:
    """Shared state container for the onboarding guide pipeline."""
    return {
        "employee_info": {},
        "research": "",
        "research_reflection": "",
        "sources": [],
        "policies": {},
        "plan": {},
        "plan_reflection": "",
        "guide": "",
        "guide_reflection": "",
        "evaluation": {},
        "judge_reflection": "",
    }


def merge_state(state: Dict[str, Any], patch: Dict[str, Any]) -> None:
    """In-place merge of agent output keys into state."""
    for key, value in patch.items():
        state[key] = value


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_dict(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


def _coerce_json_object(value: Any, field_label: str) -> Dict[str, Any]:
    """Ensure policies/plan are dicts; parse JSON strings when possible."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"{field_label}: JSON parse failed ({exc}); using empty dict")
            return {}
        if isinstance(parsed, dict):
            return parsed
        print(f"{field_label}: JSON root is not an object; wrapping under 'data'")
        return {"data": parsed}
    print(f"{field_label}: unexpected type {type(value).__name__}; using empty dict")
    return {}


def _coerce_evaluation(value: Any) -> Dict[str, Any]:
    """Normalize evaluation to a dict; parse JSON strings when possible."""
    ev: Dict[str, Any] = {}
    if isinstance(value, dict):
        ev = value
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            ev = {}
        else:
            try:
                parsed = json.loads(raw)
                ev = parsed if isinstance(parsed, dict) else {"overall_score": 0, "feedback": str(parsed)}
            except json.JSONDecodeError as exc:
                print(f"evaluation: JSON parse failed ({exc}); using minimal evaluation")
                ev = {"overall_score": 0, "feedback": raw}
    else:
        print(f"evaluation: unexpected type {type(value).__name__}; using empty dict")
        ev = {}

    # Normalize keys/defaults
    normalized = {
        "overall_score": ev.get("overall_score", ev.get("score", 0)),
        "summary": ev.get("summary", ev.get("feedback", "No summary available.")),
        "suggestions": ev.get("suggestions", ev.get("improvements", [])),
        "scores": ev.get("scores", {})
    }
    
    # Ensure suggestions is a list
    if not isinstance(normalized["suggestions"], list):
        normalized["suggestions"] = [str(normalized["suggestions"])]
        
    return normalized


def _overall_score(evaluation: Dict[str, Any]) -> float:
    raw = evaluation.get("overall_score", evaluation.get("score", 0))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def _run_with_retries(
    step_label: str,
    invoke: Callable[[], Dict[str, Any]],
    is_valid: Callable[[Dict[str, Any]], bool],
) -> Dict[str, Any]:
    """Retry agent calls when outputs are empty or fail validation."""
    max_agent_retries = _env_int("MAX_AGENT_RETRIES", 2)
    last: Dict[str, Any] = {}
    for attempt in range(max_agent_retries):
        last = invoke()
        if is_valid(last):
            return last
        if attempt < max_agent_retries - 1:
            print(f"{step_label}: empty or invalid output, retry {attempt + 2}/{max_agent_retries}")
            time.sleep(RETRY_BACKOFF_BASE_S * (attempt + 1))
    return last


def _run_guide_writer_with_retries(
    state: Dict[str, Any],
    prior_suggestions: Optional[List[str]],
) -> None:
    def invoke() -> Dict[str, Any]:
        if prior_suggestions is None:
            return guide_writer_agent(state)
        return guide_writer_agent(state, prior_suggestions=prior_suggestions)

    def valid(patch: Dict[str, Any]) -> bool:
        return _nonempty_str(patch.get("guide"))

    patch = _run_with_retries("Guide Writer Agent", invoke, valid)
    merge_state(state, patch)


def _run_judge_with_retries(state: Dict[str, Any]) -> None:
    def invoke() -> Dict[str, Any]:
        return judge_agent(state)

    def valid(patch: Dict[str, Any]) -> bool:
        ev = _coerce_evaluation(patch.get("evaluation"))
        return isinstance(ev, dict) and ev != {}

    patch = _run_with_retries("Judge Agent", invoke, valid)
    merge_state(state, patch)
    state["evaluation"] = _coerce_evaluation(state.get("evaluation"))


def run_pipeline(
    client: Optional[Any],
    employee_info: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute the onboarding pipeline: research -> policies -> plan -> guide -> judge,
    with optional guide regeneration when overall_score < 4.
    """
    if client is None:
        print("Warning: No LLM client provided. Agents will run in fallback/placeholder mode.")

    state = initial_state()
    state["client"] = client
    state["employee_info"] = dict(employee_info)

    print(f"Running Research Agent for {employee_info.get('role')}...")
    patch = _run_with_retries(
        "Research Agent",
        lambda: role_researcher_agent(state),
        lambda p: _nonempty_str(p.get("research")),
    )
    merge_state(state, patch)
    print("Research complete.")

    print("Running Policy Fetcher Agent...")
    patch = _run_with_retries(
        "Policy Fetcher Agent",
        lambda: policy_fetcher_agent(state),
        lambda p: _nonempty_dict(p.get("policies")),
    )
    merge_state(state, patch)
    state["policies"] = _coerce_json_object(state.get("policies"), "policies")

    print("Running Plan Builder Agent...")
    patch = _run_with_retries(
        "Plan Builder Agent",
        lambda: plan_builder_agent(state),
        lambda p: _nonempty_dict(p.get("plan")),
    )
    merge_state(state, patch)
    state["plan"] = _coerce_json_object(state.get("plan"), "plan")

    print("Running Guide Writer Agent...")
    _run_guide_writer_with_retries(state, prior_suggestions=None)

    print("Running Judge Agent...")
    _run_judge_with_retries(state)

    max_guide_regenerations = _env_int("MAX_GUIDE_REGENERATIONS", 1, minimum=0)
    regenerations = 0
    while _overall_score(state["evaluation"]) < 4 and regenerations < max_guide_regenerations:
        suggestions = state["evaluation"].get("suggestions") or []
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)]
        print(
            f"Judge overall_score {_overall_score(state['evaluation'])} < 4; "
            f"regenerating guide (cycle {regenerations + 1}/{max_guide_regenerations})..."
        )
        _run_guide_writer_with_retries(state, prior_suggestions=list(suggestions))
        print("Running Judge Agent...")
        _run_judge_with_retries(state)
        regenerations += 1

    return state

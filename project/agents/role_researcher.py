"""Role researcher: gathers role/domain context and citations."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List


def _fallback_research(employee_info: Dict[str, Any]) -> Dict[str, Any]:
    role = (employee_info.get("role") or "Employee").strip()
    department = (employee_info.get("department") or "General").strip()
    seniority = (employee_info.get("seniority") or "Mid-level").strip()

    summary = {
        "role": role,
        "department": department,
        "seniority": seniority,
        "role_focus": [
            f"Clarify {role} outcomes for the first 30/60/90 days.",
            f"Map {department} stakeholder expectations and cadence.",
            "Define measurable onboarding checkpoints and deliverables.",
        ],
        "recommended_day1": [
            "Access checklist verification (SSO, email, repo, collaboration tools).",
            "Manager alignment on near-term priorities and success criteria.",
            "Documentation and workflow orientation for the team.",
        ],
        "note": "Generated fallback research because live web research is unavailable.",
    }
    return {"research": json.dumps(summary, indent=2), "sources": []}


def role_researcher_agent(employee_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform lightweight role research using Tavily when available.
    Returns JSON text plus normalized source list.
    """
    api_key = (os.getenv("TAVILY_API_KEY") or "").strip()
    if not api_key:
        return _fallback_research(employee_info)

    role = (employee_info.get("role") or "Employee").strip()
    department = (employee_info.get("department") or "General").strip()
    seniority = (employee_info.get("seniority") or "Mid-level").strip()
    query = f"{seniority} {role} onboarding checklist best practices {department}"

    try:
        from tavily import TavilyClient

        max_results = max(1, int(os.getenv("TAVILY_MAX_SEARCHES", "3")))
        client = TavilyClient(api_key=api_key)
        result = client.search(query=query, max_results=max_results)
        hits = result.get("results", []) if isinstance(result, dict) else []

        sources: List[Dict[str, str]] = []
        highlights: List[str] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            title = str(hit.get("title") or "Source").strip()
            url = str(hit.get("url") or "").strip()
            content = str(hit.get("content") or "").strip()
            if url:
                sources.append({"title": title, "url": url})
            if content:
                highlights.append(content[:280])

        research_obj = {
            "role": role,
            "department": department,
            "seniority": seniority,
            "query": query,
            "highlights": highlights[:5],
            "source_count": len(sources),
        }
        return {"research": json.dumps(research_obj, indent=2), "sources": sources}
    except Exception:
        return _fallback_research(employee_info)


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator wrapper."""
    employee_info = state.get("employee_info", {})
    result = role_researcher_agent(employee_info)
    return {
        "research": result.get("research", ""),
        "sources": result.get("sources", []),
        "research_reflection": "",
    }

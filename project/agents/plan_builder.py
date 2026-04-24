"""Plan builder: produces a structured 30-60-90 day onboarding plan."""

import json
import os
import time
from typing import Any, Dict
import jsonschema


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "reflection": {"type": "string"},
        "day_30": {"type": "array", "items": {"type": "string"}},
        "day_60": {"type": "array", "items": {"type": "string"}},
        "day_90": {"type": "array", "items": {"type": "string"}},
        "tools": {"type": "array", "items": {"type": "string"}},
        "contacts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["reflection", "day_30", "day_60", "day_90", "tools", "contacts"],
}


def plan_builder_agent(client: Any, research: Any, policies: Dict[str, Any], employee_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a 30-60-90 day plan based on research and policies.
    Ensures measurable goals and role-specific tasks.
    """
    # research might be a string (from our role_researcher.run wrapper) or a dict
    research_str = research if isinstance(research, str) else json.dumps(research)
    policies_str = json.dumps(policies, indent=2)
    role = employee_info.get("role", "General Employee")
    dept = employee_info.get("department", "General")
    seniority = employee_info.get("seniority", "Mid-level")

    prompt = f"""
    Based on the following research and company policies, architect a 30-60-90 day onboarding plan.

    Employee context:
    - Role: {role}
    - Department: {dept}
    - Seniority: {seniority}
    
    Research: {research_str}
    Policies: {policies_str}
    
    Self-Critique Requirements:
    - First, reflect on the data. What are the 3 most critical success factors for this role?
    - Ensure every goal is MEASURABLE (use numbers, specific documents, or clear outcomes).
    - Ensure milestones are specific to the exact role/department and not generic advice.
    - Critique your draft: Is it too broad? Are the tools actually relevant?
    
    Return a STRICT JSON object:
    {{
        "reflection": "Your internal critique of the plan's alignment with the role and measurability",
        "day_30": ["Measurable milestones for month 1"],
        "day_60": ["Measurable milestones for month 2"],
        "day_90": ["Measurable milestones for month 3"],
        "tools": ["Access and software requirements"],
        "contacts": ["Key personnel for collaboration"]
    }}
    
    No markdown, absolute JSON only.
    """

    retries = max(1, int(os.getenv("PLAN_LLM_RETRIES", "3")))
    for attempt in range(retries):
        try:
            if hasattr(client, "chat"):  # Groq / OpenAI / Grok
                model_name = os.getenv("PLANNER_CHAT_MODEL", "llama-3.1-8b-instant")
                if hasattr(client, "base_url"):
                    base_url_str = str(client.base_url).lower()
                    if "groq.com" in base_url_str:
                        model_name = os.getenv("PLANNER_GROQ_MODEL", model_name)
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                plan = json.loads(response.choices[0].message.content)
            elif hasattr(client, "models"):  # Gemini
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                    },
                )
                plan = json.loads(response.text)
            
            jsonschema.validate(instance=plan, schema=PLAN_SCHEMA)
            return plan
        except Exception as e:
            if attempt == retries - 1:
                print(f"DEBUG: Plan Builder failed after {retries} attempts: {e}")
                return {
                    "day_30": [f"Error Generating Plan: {str(e)}"],
                    "day_60": [],
                    "day_90": [],
                    "tools": [],
                    "contacts": [],
                }
            time.sleep(1)

    return {
        "day_30": ["No plan generated after repeated failures."],
        "day_60": [],
        "day_90": [],
        "tools": [],
        "contacts": [],
    }


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator wrapper."""
    client = state.get("client")
    research = state.get("research", "")
    policies = state.get("policies", {})
    employee_info = state.get("employee_info", {})
    
    plan = plan_builder_agent(client, research, policies, employee_info)
    return {
        "plan": plan,
        "plan_reflection": plan.get("reflection", "")
    }

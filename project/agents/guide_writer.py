"""Guide writer: turns the plan and context into a polished Markdown onboarding guide."""

import json
import os
import time
from typing import Any, Dict, List, Optional


def guide_writer_agent(client: Any, plan: Dict[str, Any], employee_info: Dict[str, Any], prior_suggestions: Optional[List[str]] = None) -> str:
    """
    Generate a Markdown onboarding guide with human-professional tone.
    Sections: Welcome, Day 1 checklist, Tools, 30/60/90 plan, Contacts.
    """
    name = employee_info.get("name") or "[New Employee Name]"
    role = employee_info.get("role") or "[Role]"
    dept = employee_info.get("department") or "[Department]"
    
    plan_str = ""
    try:
        plan_str = json.dumps(plan, indent=2)
    except:
        plan_str = str(plan)

    prompt = f"""
    You are a professional Onboarding Architect. Execute a self-reflective writing process.
    
    1. Plan: How will you structure this guide to be both welcoming and highly professional for a {role}?
    2. Draft: Create a draft based on the context data.
    3. Critique: Review your draft. Is it too repetitive? Does it sound robotic? Is it missing any Day 1 essentials?
    4. Refine: Finalize the polished guide.

    Employee Context:
    - Name: {name}
    - Role: {role}
    - Department: {dept}

    Context Data (Plan):
    {plan_str}
    
    Structure:
    1. Welcome
    2. Day 1 Checklist
    3. Tools & Access
    4. 30/60/90 Milestones
    5. Key Contacts
    
    Rules:
    - Incorporate prior suggestions: {prior_suggestions if prior_suggestions else 'None'}.
    - Use a human-professional, classy tone.
    - Avoid generic statements; every section must include role-specific and department-specific details.
    - Include concrete Day 1 tasks, exact tools/access, and measurable 30/60/90 milestones.
    - Do not use placeholders like "TBD" or "[Role]".
    
    Output Format:
    <reflection>Your internal planning and critique</reflection>
    [MARKDOWN GUIDE STARTS HERE]
    """

    retries = max(1, int(os.getenv("GUIDE_LLM_RETRIES", "3")))
    for attempt in range(retries):
        try:
            if hasattr(client, "chat"):  # Groq / OpenAI / Grok
                model_name = os.getenv("GUIDE_CHAT_MODEL", "llama-3.1-8b-instant")
                if hasattr(client, "base_url"):
                    base_url_str = str(client.base_url).lower()
                    if "groq.com" in base_url_str:
                        model_name = os.getenv("GUIDE_GROQ_MODEL", model_name)
                    elif "x.ai" in base_url_str:
                        model_name = os.getenv("GUIDE_XAI_MODEL", "grok-beta")
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content
            elif hasattr(client, "models"):  # Gemini
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                return response.text
        except Exception as e:
            if attempt == retries - 1:
                print(f"DEBUG: Guide Writer failed after {retries} attempts: {e}")
                return f"# Error Generating Guide\n\n**The AI failed with the following message:**\n\n`{str(e)}`"
            time.sleep(1)

    return f"# Welcome {name}\n\nWe encountered a repeated error generating your guide. Check the logs for details."


def run(state: Dict[str, Any], prior_suggestions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Orchestrator wrapper."""
    client = state.get("client")
    plan = state.get("plan", {})
    employee_info = state.get("employee_info", {})
    
    full_guide = guide_writer_agent(client, plan, employee_info, prior_suggestions=prior_suggestions)
    
    reflection = ""
    guide = full_guide
    
    # Extract reflection for the UI
    if "<reflection>" in full_guide and "</reflection>" in full_guide:
        reflection = full_guide.split("<reflection>")[1].split("</reflection>")[0].strip()
        guide = full_guide.split("</reflection>")[-1].strip()
    
    return {
        "guide": guide,
        "guide_reflection": reflection
    }

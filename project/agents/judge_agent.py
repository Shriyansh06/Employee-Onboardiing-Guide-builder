"""Judge agent: evaluates the guide and provides feedback."""

import json
import os
import time
from typing import Any, Dict


def judge_agent(client: Any, guide: str, employee_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score the guide based on quality, relevance, and tone.
    Returns: JSON with scores, overall_score, summary, and improvements.
    """
    prompt = f"""
    You are a meticulous Quality Assurance Judge. Perform a self-critical evaluation.
    
    1. Analysis: Review the guide for tone, completeness, and actionability for a {employee_info.get('seniority')} {employee_info.get('role')}.
    2. Internal Critique: Are your scores consistent? Are you being too lenient or too harsh?
    3. Final Judgment: Provide the score and actionable suggestions.

    Guide to Evaluate:
    {guide}
    
    Return a STRICT JSON object:
    {{
        "reflection": "An internal analysis of the guide's strengths/weaknesses and your scoring rationale",
        "scores": {{
            "tone": 0-10,
            "completeness": 0-10,
            "actionability": 0-10,
            "professionalism": 0-10
        }},
        "overall_score": 0-10,
        "summary": "High-level professional summary",
        "improvements": ["List of 2-3 critical refinements"]
    }}
    
    No markdown, absolute JSON only.
    """

    retries = max(1, int(os.getenv("JUDGE_LLM_RETRIES", "3")))
    for attempt in range(retries):
        try:
            if hasattr(client, "chat"):  # Groq / OpenAI / Grok
                model_name = os.getenv("JUDGE_CHAT_MODEL", "llama-3.1-8b-instant")
                if hasattr(client, "base_url"):
                    base_url_str = str(client.base_url).lower()
                    if "groq.com" in base_url_str:
                        model_name = os.getenv("JUDGE_GROQ_MODEL", model_name)
                    elif "x.ai" in base_url_str:
                        model_name = os.getenv("JUDGE_XAI_MODEL", "grok-beta")
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                return json.loads(response.choices[0].message.content)
            elif hasattr(client, "models"):  # Gemini
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                    },
                )
                return json.loads(response.text)
        except Exception as e:
            if attempt == retries - 1:
                print(f"DEBUG: Judge Agent failed after {retries} attempts: {e}")
                return {
                    "scores": {"tone": 0, "completeness": 0, "actionability": 0, "professionalism": 0},
                    "overall_score": 0,
                    "summary": f"Evaluation Error: {str(e)}",
                    "improvements": ["Check your API key and model access on Groq."]
                }
            time.sleep(1)

    return {
        "scores": {"tone": 0, "completeness": 0, "actionability": 0, "professionalism": 0},
        "overall_score": 0,
        "summary": "Evaluation failed repeatedly.",
        "improvements": ["Try again in a few minutes."]
    }


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator wrapper."""
    client = state.get("client")
    guide = state.get("guide", "")
    employee_info = state.get("employee_info", {})
    
    if not client:
        return {"evaluation": {}}
        
    evaluation = judge_agent(client, guide, employee_info)
    
    # Bridge to orchestrator expected fields:
    if "improvements" in evaluation:
        evaluation["suggestions"] = evaluation["improvements"]
        
    return {
        "evaluation": evaluation,
        "judge_reflection": evaluation.get("reflection", "")
    }

"""Policy fetcher: loads company policies relevant to onboarding."""

import json
import os
from typing import Any, Dict


def policy_fetcher_agent(employee_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load JSON from file and map to categories based on department.
    Logic:
    - Engineering -> IT + Compliance
    - HR -> HR policies + Benefits
    """
    dept = employee_info.get("department", "").lower()
    
    # Path to data
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "company_policies.json")
    
    try:
        with open(data_path, "r") as f:
            all_policies = json.load(f)
    except Exception as e:
        print(f"Error loading policies: {e}")
        all_policies = {}

    result = {
        "IT_SETUP": {},
        "HR_POLICIES": {},
        "COMPLIANCE": {},
        "BENEFITS": {}
    }

    IT_BASIC = all_policies.get("IT_SETUP", {})
    HR_BASIC = all_policies.get("HR_POLICIES", {})
    COMP_BASIC = all_policies.get("COMPLIANCE", {})
    BENE_BASIC = all_policies.get("BENEFITS", {})

    # Engineering logic
    if "eng" in dept or "soft" in dept or "dev" in dept:
        result["IT_SETUP"] = IT_BASIC
        result["COMPLIANCE"] = COMP_BASIC
        result["HR_POLICIES"] = HR_BASIC # Include basic HR for everyone
    
    # HR logic
    elif "hr" in dept or "human" in dept or "talent" in dept:
        result["HR_POLICIES"] = HR_BASIC
        result["BENEFITS"] = BENE_BASIC
        result["COMPLIANCE"] = COMP_BASIC
    
    # Marketing / Sales / Others fallback
    else:
        result["IT_SETUP"] = {
            "general": {
                "vpn_access": IT_BASIC.get("vpn_access", "Contact IT for setup.")
            }
        }
        result["HR_POLICIES"] = HR_BASIC
        result["BENEFITS"] = BENE_BASIC

    # Ensure result keys exist and aren't empty
    for key in ["IT_SETUP", "HR_POLICIES", "COMPLIANCE", "BENEFITS"]:
        if not result.get(key):
            result[key] = {"note": f"Standard {key.lower().replace('_', ' ')} applies."}

    return result


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator wrapper."""
    employee_info = state.get("employee_info", {})
    policies = policy_fetcher_agent(employee_info)
    return {"policies": policies}

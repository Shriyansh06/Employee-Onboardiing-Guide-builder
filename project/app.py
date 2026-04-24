"""
Luxury Minimalist Streamlit entry point for the Onboarding Intelligence suite.
Strict monochrome theme, zero emojis, and premium typography.
"""

import os
import json
import time
from datetime import date
from typing import Any, Dict, Optional

import streamlit as st
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from orchestrator import run_pipeline

# Constants
SENIORITY_OPTIONS = ["Intern", "Junior", "Mid-level", "Senior", "Staff", "Principal", "Lead", "Executive"]
APP_TITLE = "Onboarding Intelligence"


def apply_generation_profile(profile: str) -> None:
    """Set runtime tuning knobs for speed vs output quality."""
    if profile == "Accurate":
        os.environ["MAX_AGENT_RETRIES"] = "3"
        os.environ["MAX_GUIDE_REGENERATIONS"] = "2"
        os.environ["TAVILY_MAX_SEARCHES"] = "5"
        os.environ["TAVILY_SEARCH_RETRIES"] = "3"
        os.environ["RESEARCH_LLM_RETRIES"] = "3"
        os.environ["PLAN_LLM_RETRIES"] = "3"
        os.environ["GUIDE_LLM_RETRIES"] = "3"
        os.environ["JUDGE_LLM_RETRIES"] = "3"
        os.environ["PLANNER_GROQ_MODEL"] = "llama-3.3-70b-versatile"
        os.environ["GUIDE_GROQ_MODEL"] = "llama-3.3-70b-versatile"
        os.environ["JUDGE_GROQ_MODEL"] = "llama-3.3-70b-versatile"
    elif profile == "Balanced":
        os.environ["MAX_AGENT_RETRIES"] = "2"
        os.environ["MAX_GUIDE_REGENERATIONS"] = "1"
        os.environ["TAVILY_MAX_SEARCHES"] = "3"
        os.environ["TAVILY_SEARCH_RETRIES"] = "2"
        os.environ["RESEARCH_LLM_RETRIES"] = "2"
        os.environ["PLAN_LLM_RETRIES"] = "2"
        os.environ["GUIDE_LLM_RETRIES"] = "2"
        os.environ["JUDGE_LLM_RETRIES"] = "2"
    else:
        os.environ["MAX_AGENT_RETRIES"] = "1"
        os.environ["MAX_GUIDE_REGENERATIONS"] = "0"
        os.environ["TAVILY_MAX_SEARCHES"] = "2"
        os.environ["TAVILY_SEARCH_RETRIES"] = "1"
        os.environ["RESEARCH_LLM_RETRIES"] = "1"
        os.environ["PLAN_LLM_RETRIES"] = "1"
        os.environ["GUIDE_LLM_RETRIES"] = "1"
        os.environ["JUDGE_LLM_RETRIES"] = "1"

# --- UI Styling ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        :root {
            --bg-color: #000000;
            --card-bg: #0a0a0a;
            --accent-color: #ffffff;
            --border-color: #262626;
            --text-main: #ffffff;
            --text-dim: #737373;
        }

        .stApp {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
        }

        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            color: var(--text-main) !important;
            letter-spacing: -0.02em;
        }

        .main-header {
            text-align: center;
            padding: 3rem 0;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 3rem;
        }

        .stTextArea textarea {
            background-color: var(--bg-color) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 4px !important;
            font-size: 1rem !important;
        }
        
        .stTextArea textarea:focus {
            border-color: var(--accent-color) !important;
        }

        .stButton button {
            background-color: var(--accent-color) !important;
            color: var(--bg-color) !important;
            border: none !important;
            padding: 0.5rem 2rem !important;
            border-radius: 2px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }

        .stButton button:hover {
            opacity: 0.9;
            background-color: #e5e5e5 !important;
        }

        .metric-card {
            background: var(--card-bg);
            padding: 2rem;
            border-radius: 4px;
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }
        
        .timer-badge {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-dim);
            text-align: right;
            margin-bottom: 1rem;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #000000;
            border-right: 1px solid var(--border-color);
        }
    </style>
    """, unsafe_allow_html=True)

# --- AI Client Setup ---
@st.cache_resource
def get_gemini_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)

@st.cache_resource
def get_llm_client(api_key: str) -> OpenAI:
    base_url = "https://api.x.ai/v1"
    if api_key.startswith("gsk_"):
        base_url = "https://api.groq.com/openai/v1"
    return OpenAI(api_key=api_key, base_url=base_url)

def extract_employee_info(client: Any, text: str) -> Dict[str, Any]:
    prompt = f"""
    Extract employee details from the following text:
    "{text}"

    Return a STRICT JSON object with these keys:
    - name: string
    - role: string
    - department: string (default "General")
    - seniority: One of {SENIORITY_OPTIONS} (choose best fit, default "Mid-level")
    
    No markdown, just JSON.
    """
    
    try:
        if hasattr(client, "chat"):
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant" if "groq.com" in str(getattr(client, "base_url", "")) else "grok-beta",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        elif hasattr(client, "models"):
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(resp.text)
    except Exception as e:
        st.error(f"Data extraction failed: {e}")
    
    return {"name": "New Employee", "role": "Specialist", "department": "General", "seniority": "Mid-level"}

# --- Main App ---
def main():
    load_dotenv()
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")
    inject_custom_css()

    # Sidebar: Config & Status
    with st.sidebar:
        st.title("Configuration")
        generation_profile = st.selectbox(
            "Generation Profile",
            ["Fast", "Balanced", "Accurate"],
            index=2,
            help="Accurate gives more specific output but takes longer.",
        )
        apply_generation_profile(generation_profile)
        
        gemini_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
        groq_key = (os.getenv("GROQ_API_KEY") or os.getenv("XAI_API_KEY") or "").strip()
        
        client = None
        if groq_key:
            client = get_llm_client(groq_key)
            provider = "Groq" if groq_key.startswith("gsk_") else "xAI"
            st.success(f"Provider: {provider}")
        elif gemini_key:
            client = get_gemini_client(gemini_key)
            st.success("Provider: Gemini")
        else:
            st.warning("No API Keys identified in .env")

    # Header
    st.markdown(f'<div class="main-header"><h1>{APP_TITLE.upper()}</h1><p style="color:#737373; text-transform:uppercase; letter-spacing:0.15em; font-size:0.8rem">Intelligent Personnel Onboarding Architecture</p></div>', unsafe_allow_html=True)

    # Main Input Area
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("### Context Input")
        user_input = st.text_area(
            "Describe the personnel status and role requirements",
            placeholder="Example: Jane Doe is joining as a Senior Software Engineer in the Infrastructure team...",
            height=150,
            label_visibility="collapsed"
        )
        
        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            generate_btn = st.button("Generate Guide")

    # Workflow Execution
    if generate_btn:
        if not user_input.strip():
            st.error("Input required for synthesis.")
            return
        
        if not client:
            st.error("Client configuration missing.")
            return

        with st.spinner("Processing..."):
            start_time = time.perf_counter()
            
            # Step 1: Extraction
            info = extract_employee_info(client, user_input)
            info["start_date"] = date.today().isoformat()
            
            # Step 2: Pipeline
            try:
                state = run_pipeline(client, info)
                end_time = time.perf_counter()
                
                st.session_state["onboarding_state"] = state
                st.session_state["gen_duration"] = end_time - start_time
                st.toast("Synthesis complete.")
            except Exception as e:
                st.error(f"Synthesis error: {e}")

    # Results Dashboard
    if "onboarding_state" in st.session_state:
        state = st.session_state["onboarding_state"]
        duration = st.session_state.get("gen_duration", 0)
        
        st.markdown(f'<div class="timer-badge">Process duration: {duration:.2f}s</div>', unsafe_allow_html=True)
        
        main_col, side_col = st.columns([3, 1])

        with main_col:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown("### PERSONNEL ONBOARDING GUIDE")
            st.markdown("---")
            st.markdown(state.get("guide", "No content generated."))
            
            # Hidden References at the bottom (Perplexity Style but hidden)
            sources = state.get("sources", [])
            if sources:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("REFERENCES"):
                    for src in sources:
                        st.markdown(f"- [{src.get('title', 'Source')}]({src.get('url', '#')})")
            st.markdown('</div>', unsafe_allow_html=True)

        with side_col:
            st.markdown("### ANALYTICS")
            eval_data = state.get("evaluation", {})
            
            if eval_data:
                score = eval_data.get("overall_score", 0)
                st.markdown(f'<div class="metric-card"><h2 style="text-align:center; color:#ffffff !important">{score}/10</h2><p style="text-align:center; margin:0; text-transform:uppercase; font-size:0.7rem; color:#737373">Quality Index</p></div>', unsafe_allow_html=True)
                
                scores = eval_data.get("scores", {})
                for k, v in scores.items():
                    st.write(f"**{k.upper()}**")
                    st.progress(v / 10.0)
                
                st.markdown("---")
                st.markdown("**SUMMARY**")
                st.info(eval_data.get("summary", "Analysis complete."))
                
                improvements = eval_data.get("suggestions", [])
                if improvements:
                    with st.expander("OPTIMIZATIONS"):
                        for imp in improvements:
                            st.write(f"- {imp}")
            else:
                st.warning("Analysis unavailable.")

if __name__ == "__main__":
    main()

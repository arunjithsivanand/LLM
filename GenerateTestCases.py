from dotenv import load_dotenv
import pandas as pd
from io import StringIO
import re
import os
import hashlib
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

st.set_page_config(
    page_title="Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize LLM once at startup
@st.cache_resource
def initialize_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-pro",  # Using faster model
        temperature=0.3,
        max_output_tokens=2048,  # Reduced token limit
        top_p=0.95,
        top_k=40,
    )

# Cache test case generation based on input parameters
@st.cache_data(ttl=3600)  # Cache for 1 hour
def generate_test_cases_cached(module, acceptance_criteria, scenario_type):
    try:
        llm = initialize_llm()
        prompt = f"""Create 3 test cases for:
Module: {module}
Acceptance Criteria: {acceptance_criteria}
Scenario Type: {scenario_type}

Format each test case as:
Test Case ID: TC-XXX
Description: [brief description]
Pre-conditions: [pre-conditions]
Steps: [numbered steps]
Expected Results: [expected outcome]
Tags: [relevant tags]

Be concise and specific."""
        
        response = llm.invoke(prompt)
        return response.content if response and hasattr(response, "content") else None
    except Exception as e:
        return f"Error: {str(e)}"

@st.cache_data
def parse_test_cases(text):
    if not text or "Error:" in text:
        return []
        
    test_cases = []
    current_case = {}
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            if current_case:
                test_cases.append(current_case)
                current_case = {}
            continue

        if line.startswith(('Test Case ID:', 'TC-')):
            if current_case:
                test_cases.append(current_case)
            current_case = {'Test Case ID': line.split(':', 1)[-1].strip()}
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            key_map = {
                'description': 'Description',
                'pre-condition': 'Pre-conditions',
                'step': 'Steps',
                'expected': 'Expected Results',
                'post-condition': 'Post-conditions',
                'tag': 'Tags'
            }
            
            for k, v in key_map.items():
                if k in key.lower():
                    current_case[v] = value
                    break

    if current_case:
        test_cases.append(current_case)
    return test_cases

def create_download_button(df, module_name):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    st.download_button(
        label="📥 Download Test Cases (CSV)",
        data=csv_data,
        file_name=f"{module_name}_test_cases.csv",
        mime="text/csv",
        key="download_button",
        use_container_width=True
    )

def main():
    st.markdown("""
        <h1>🧪 Quick Test Case Generator</h1>
        <p style='font-size: 1.2em; color: #666; margin-bottom: 1rem;'>
            Generate test cases instantly
        </p>
    """, unsafe_allow_html=True)

    # Input Section with more compact layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        module = st.text_input(
            "Module Name",
            placeholder="Enter module name...",
            key="module_input"
        )
        
        acceptance_criteria = st.text_area(
            "Acceptance Criteria",
            placeholder="Enter acceptance criteria...",
            height=100,
            key="acceptance_criteria_input"
        )

    with col2:
        scenario_type = st.selectbox(
            "Scenario Type",
            ["Positive Scenarios", "Negative Scenarios", "All Scenarios"],
            index=0,  # Default to positive scenarios
            key="scenario_type_input"
        )
        
        generate_button = st.button(
            "🚀 Generate",
            key="generate_button",
            use_container_width=True,
            type="primary"
        )

    # Results Section
    if generate_button:
        if not module or not acceptance_criteria:
            st.warning("Please fill in all required fields.")
            return

        # Show a placeholder for results immediately
        results_placeholder = st.empty()
        download_placeholder = st.empty()
        
        with st.spinner(""):  # Empty spinner text for cleaner look
            # Generate test cases with caching
            test_cases = generate_test_cases_cached(module, acceptance_criteria, scenario_type)
            
            if test_cases and "Error:" not in test_cases:
                # Parse and create DataFrame
                parsed_cases = parse_test_cases(test_cases)
                if parsed_cases:
                    df = pd.DataFrame(parsed_cases)
                    
                    # Update UI with results
                    with results_placeholder.expander("View Generated Test Cases", expanded=True):
                        st.text_area(
                            "",  # No label needed
                            value=test_cases,
                            height=200,
                            key="results",
                            disabled=True
                        )
                    
                    with download_placeholder:
                        create_download_button(df, module)
                        st.success(f"Generated {len(parsed_cases)} test cases")
                else:
                    st.error("No valid test cases generated. Please try again.")
            else:
                st.error(test_cases if "Error:" in str(test_cases) else "Failed to generate test cases.")

if __name__ == "__main__":
    main()

from dotenv import load_dotenv
import pandas as pd
from io import StringIO
import re
import os
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

@st.cache_data
def parse_test_cases(text):
    test_cases = []
    current_case = {}
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            if current_case:
                test_cases.append(current_case)
                current_case = {}
            continue

        if line.startswith(('Test Case ID:', 'TC-', '#')):
            if current_case:
                test_cases.append(current_case)
            current_case = {'Test Case ID': line.split(':', 1)[-1].strip()}
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            if 'description' in key.lower():
                current_case['Description'] = value
            elif 'pre-condition' in key.lower():
                current_case['Pre-conditions'] = value
            elif 'step' in key.lower():
                current_case['Steps'] = value
            elif 'expected' in key.lower():
                current_case['Expected Results'] = value
            elif 'post-condition' in key.lower():
                current_case['Post-conditions'] = value
            elif 'tag' in key.lower():
                current_case['Tags'] = value

    if current_case:
        test_cases.append(current_case)
    return test_cases

@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
        max_output_tokens=4096,
    )

@st.cache_data
def get_prompt_template():
    return PromptTemplate(
        input_variables=["Module", "AcceptanceCriteria", "ScenarioType"],
        template=(
            "Generate test cases based on the following:\n"
            "Module: {Module}\n"
            "Acceptance Criteria: {AcceptanceCriteria}\n"
            "Scenario Type: {ScenarioType}\n\n"
            "Output each test case in this exact format:\n"
            "Test Case ID: TC-XXX\n"
            "Description: [Test case description]\n"
            "Pre-conditions: [List pre-conditions]\n"
            "Steps: [Numbered steps to execute]\n"
            "Expected Results: [Expected outcome]\n"
            "Post-conditions: [List post-conditions]\n"
            "Tags: [Relevant tags]\n\n"
            "Generate at least 3 test cases, each separated by a blank line."
        ),
    )

def generate_test_cases(_module, _acceptance_criteria, _scenario_type):
    try:
        llm = get_llm()
        prompt_template = get_prompt_template()
        prompt = prompt_template.format(
            Module=_module,
            AcceptanceCriteria=_acceptance_criteria,
            ScenarioType=_scenario_type
        )
        response = llm.invoke(prompt)
        return response.content if response and hasattr(response, "content") else None
    except Exception as e:
        st.error(f"Error generating test cases: {str(e)}")
        return None

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
        <h1>🧪 Test Case Generator</h1>
        <p style='font-size: 1.2em; color: #666; margin-bottom: 2rem;'>
            Generate test cases quickly and download as CSV
        </p>
    """, unsafe_allow_html=True)

    # Input Section
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
            ["All Scenarios", "Positive Scenarios", "Negative Scenarios"],
            key="scenario_type_input"
        )
        
        generate_button = st.button(
            "🚀 Generate Test Cases",
            key="generate_button",
            use_container_width=True
        )

    # Results Section
    if generate_button:
        if not module or not acceptance_criteria:
            st.warning("Please fill in all required fields.")
            return

        with st.spinner("Generating test cases..."):
            test_cases = generate_test_cases(module, acceptance_criteria, scenario_type)
            
            if test_cases:
                # Store in session state for reuse
                st.session_state.last_test_cases = test_cases
                st.session_state.last_module = module
                
                # Display results in a clean format
                with st.expander("View Generated Test Cases", expanded=True):
                    st.text_area(
                        "Generated Test Cases",
                        value=test_cases,
                        height=300,
                        key="results",
                        disabled=True
                    )
                
                # Create DataFrame and download button
                parsed_cases = parse_test_cases(test_cases)
                if parsed_cases:
                    df = pd.DataFrame(parsed_cases)
                    create_download_button(df, module)
                    
                    # Display summary
                    st.success(f"✅ Generated {len(parsed_cases)} test cases successfully!")
                else:
                    st.error("Failed to parse test cases into CSV format.")

if __name__ == "__main__":
    main()

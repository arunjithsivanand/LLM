from dotenv import load_dotenv
import pandas as pd
from io import StringIO
import re
import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import signal

# Load environment variables
load_dotenv()

# API Key for Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Streamlit configuration
st.set_page_config(
    page_title="Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Test case generation timed out.")

# Parse test cases into structured format
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

# Initialize LLM
@st.cache_resource
def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
        max_output_tokens=2048  # Reduced token limit for faster generation
    )

# Prompt template
@st.cache_data
def get_prompt_template():
    return PromptTemplate(
        input_variables=["Module", "AcceptanceCriteria", "ScenarioType"],
        template=(
            "Generate detailed test cases based on the following:\n"
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
            "Generate multiple test cases, with each separated by a blank line."
        ),
    )

# Generate test cases
@st.cache_data
def generate_test_cases(module, acceptance_criteria, scenario_type):
    llm = get_llm()
    prompt_template = get_prompt_template()
    prompt = prompt_template.format(
        Module=module,
        AcceptanceCriteria=acceptance_criteria,
        ScenarioType=scenario_type
    )
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30-second timeout

    try:
        response = llm.invoke(prompt)
        signal.alarm(0)  # Cancel timeout
        return response.content if response and hasattr(response, "content") else None
    except TimeoutError:
        st.error("Test case generation timed out. Please try again with simpler inputs.")
        return None

# Export data to CSV
def export_to_csv(df, module_name):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    st.download_button(
        label="Download Test Cases as CSV",
        data=csv_data,
        file_name=f"{module_name}_test_cases.csv",
        mime="text/csv",
        key="download_button"
    )

# Render the header section
def render_header():
    st.markdown("""
        <h1>🧪 Advanced Test Case Generator</h1>
        <p style='text-align: center; font-size: 1.2em; color: #666; margin-bottom: 2rem;'>
            Generate comprehensive test cases with intelligent scenario coverage
        </p>
    """, unsafe_allow_html=True)

# Input section
def input_section():
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("##### 📦 Module Information")
        module = st.text_input(
            "Module Name",
            placeholder="Enter module name...",
            help="Enter the name of the module you want to test",
            key="module_input"
        )

    with col2:
        st.markdown("##### 🎯 Test Coverage")
        scenario_type = st.selectbox(
            "Scenario Type",
            ["All Scenarios", "Positive Scenarios", "Negative Scenarios"],
            help="Select the type of test scenarios to generate",
            key="scenario_type_input"
        )

    with col3:
        st.markdown("##### ✅ Requirements")
        acceptance_criteria = st.text_area(
            "Acceptance Criteria",
            placeholder="Enter acceptance criteria...",
            help="Enter the acceptance criteria for the module",
            height=100,
            key="acceptance_criteria_input"
        )
    
    return module, scenario_type, acceptance_criteria

# Main function
def main():
    if 'generation_requested' not in st.session_state:
        st.session_state.generation_requested = False

    render_header()

    # Get inputs
    module, scenario_type, acceptance_criteria = input_section()

    if st.button("Generate Test Cases", key="generate_button"):
        st.session_state.generation_requested = True
        st.session_state.module = module
        st.session_state.scenario_type = scenario_type
        st.session_state.acceptance_criteria = acceptance_criteria

    if st.session_state.generation_requested:
        if st.session_state.module and st.session_state.acceptance_criteria:
            with st.spinner("Generating test cases..."):
                test_cases = generate_test_cases(
                    st.session_state.module,
                    st.session_state.acceptance_criteria,
                    st.session_state.scenario_type
                )
                
                if test_cases:
                    st.write("### Generated Test Cases:")
                    st.write(test_cases)

                    parsed_test_cases = parse_test_cases(test_cases)
                    if parsed_test_cases:
                        df = pd.DataFrame(parsed_test_cases)
                        export_to_csv(df, st.session_state.module)
                    else:
                        st.error("Failed to parse test cases. Please check the generated format.")
        else:
            st.warning("Please fill in all required fields.")

if __name__ == "__main__":
    main()

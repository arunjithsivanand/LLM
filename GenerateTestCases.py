from dotenv import load_dotenv
import pandas as pd
from io import StringIO
import re
import os
import time
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

# Add timeout settings
GENERATION_TIMEOUT = 60  # seconds
CHUNK_SIZE = 2  # number of scenarios to generate per chunk

@st.cache_data
def parse_test_cases(text):
    """Parse the generated test cases into a structured format"""
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

def get_prompt_template(chunk_number=None):
    base_template = (
        "Generate {chunk_size} detailed test cases based on the following:\n"
        "Module: {Module}\n"
        "Acceptance Criteria: {AcceptanceCriteria}\n"
        "Scenario Type: {ScenarioType}\n"
    )
    
    if chunk_number is not None:
        base_template += f"\nGenerate different test cases from previous chunks. This is chunk {chunk_number}.\n"
    
    base_template += (
        "\nOutput each test case in this exact format:\n"
        "Test Case ID: TC-XXX\n"
        "Description: [Test case description]\n"
        "Pre-conditions: [List pre-conditions]\n"
        "Steps: [Numbered steps to execute]\n"
        "Expected Results: [Expected outcome]\n"
        "Post-conditions: [List post-conditions]\n"
        "Tags: [Relevant tags]\n\n"
    )
    
    return PromptTemplate(
        input_variables=["Module", "AcceptanceCriteria", "ScenarioType", "chunk_size"],
        template=base_template,
    )

def generate_test_cases_in_chunks(_module, _acceptance_criteria, _scenario_type, num_chunks=3):
    llm = get_llm()
    all_test_cases = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for i in range(num_chunks):
            status_text.text(f"Generating chunk {i+1}/{num_chunks}...")
            
            prompt_template = get_prompt_template(chunk_number=i+1)
            prompt = prompt_template.format(
                Module=_module,
                AcceptanceCriteria=_acceptance_criteria,
                ScenarioType=_scenario_type,
                chunk_size=CHUNK_SIZE
            )
            
            # Add timeout handling
            start_time = time.time()
            while True:
                try:
                    response = llm.invoke(prompt)
                    if response and hasattr(response, "content"):
                        all_test_cases.append(response.content)
                    break
                except Exception as e:
                    if time.time() - start_time > GENERATION_TIMEOUT:
                        raise TimeoutError("Test case generation timed out")
                    time.sleep(1)  # Wait before retry
            
            progress_bar.progress((i + 1) / num_chunks)
            
            # Add a small delay to prevent rate limiting
            time.sleep(0.5)
        
        status_text.text("Processing generated test cases...")
        combined_test_cases = "\n\n".join(all_test_cases)
        status_text.empty()
        progress_bar.empty()
        
        return combined_test_cases
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Error generating test cases: {str(e)}")
        return None

def render_header():
    st.markdown("""
        <h1>🧪 Advanced Test Case Generator</h1>
        <p style='text-align: center; font-size: 1.2em; color: #666; margin-bottom: 2rem;'>
            Generate comprehensive test cases with intelligent scenario coverage
        </p>
    """, unsafe_allow_html=True)

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
    
    # Add number of test cases slider
    num_chunks = st.slider(
        "Number of Test Case Chunks",
        min_value=1,
        max_value=5,
        value=3,
        help="Each chunk generates 2 test cases. More chunks = more variety but longer generation time."
    )
    
    return module, scenario_type, acceptance_criteria, num_chunks

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

def main():
    if 'generation_requested' not in st.session_state:
        st.session_state.generation_requested = False

    render_header()

    module, scenario_type, acceptance_criteria, num_chunks = input_section()

    if st.button("Generate Test Cases", key="generate_button"):
        st.session_state.generation_requested = True
        st.session_state.module = module
        st.session_state.scenario_type = scenario_type
        st.session_state.acceptance_criteria = acceptance_criteria
        st.session_state.num_chunks = num_chunks

    if st.session_state.generation_requested:
        if st.session_state.module and st.session_state.acceptance_criteria:
            test_cases = generate_test_cases_in_chunks(
                st.session_state.module,
                st.session_state.acceptance_criteria,
                st.session_state.scenario_type,
                st.session_state.num_chunks
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

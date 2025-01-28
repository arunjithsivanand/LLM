from dotenv import load_dotenv
import pandas as pd
from io import StringIO
import re
import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Streamlit app configuration
st.set_page_config(
    page_title="Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_data
def parse_test_cases(text):
    """Parse the generated test cases into a structured format."""
    test_cases = []
    current_case = {}

    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:  # Skip empty lines
            if current_case:
                test_cases.append(current_case)
                current_case = {}
            continue

        # Identify the start of a new test case
        if re.match(r"^(Test Case ID|TC-|#)", line):
            if current_case:
                test_cases.append(current_case)
            current_case = {"Test Case ID": line.split(":", 1)[-1].strip()}

        # Handle key-value pairs
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if "description" in key.lower():
                current_case["Description"] = value
            elif "pre-condition" in key.lower():
                current_case["Pre-conditions"] = value
            elif "step" in key.lower():
                current_case["Steps"] = value
            elif "expected" in key.lower():
                current_case["Expected Results"] = value
            elif "post-condition" in key.lower():
                current_case["Post-conditions"] = value
            elif "tag" in key.lower():
                current_case["Tags"] = value

    # Add the last test case if it exists
    if current_case:
        test_cases.append(current_case)

    # Ensure all keys are present in every test case
    required_keys = ["Test Case ID", "Description", "Pre-conditions", "Steps", "Expected Results", "Post-conditions", "Tags"]
    for case in test_cases:
        for key in required_keys:
            case.setdefault(key, "N/A")

    return test_cases

@st.cache_resource
def get_llm():
    """Initialize the Google Generative AI model."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
        max_output_tokens=4096,
    )

@st.cache_data
def get_prompt_template():
    """Create the prompt template for generating test cases."""
    return PromptTemplate(
        input_variables=["Module", "AcceptanceCriteria", "ScenarioType"],
        template=(
            "Generate detailed test cases based on the following:\n"
            "Module: {Module}\n"
            "Acceptance Criteria: {AcceptanceCriteria}\n"
            "Scenario Type: {ScenarioType}\n\n"
            "Strictly follow this output format:\n"
            "Test Case ID: TC-XXX\n"
            "Description: [Test case description]\n"
            "Pre-conditions: [List pre-conditions]\n"
            "Steps: [Numbered steps to execute]\n"
            "Expected Results: [Expected outcome]\n"
            "Post-conditions: [List post-conditions]\n"
            "Tags: [Relevant tags]\n\n"
            "Each test case must follow this format exactly. Do not deviate from it."
        ),
    )

def render_header():
    """Render the header section of the app."""
    st.markdown("""
        <h1>🧪 Advanced Test Case Generator</h1>
        <p style='text-align: center; font-size: 1.2em; color: #666; margin-bottom: 2rem;'>
            Generate comprehensive test cases with intelligent scenario coverage
        </p>
    """, unsafe_allow_html=True)

def input_section():
    """Render the input section for the app."""
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

@st.cache_data
def generate_test_cases(_module, _acceptance_criteria, _scenario_type):
    """Generate test cases using the LLM."""
    llm = get_llm()
    prompt_template = get_prompt_template()
    prompt = prompt_template.format(
        Module=_module,
        AcceptanceCriteria=_acceptance_criteria,
        ScenarioType=_scenario_type
    )
    response = llm.invoke(prompt)
    return response.content if response and hasattr(response, "content") else None

def export_to_csv(df, module_name):
    """Export the test cases to a CSV file."""
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
    """Main function to run the Streamlit app."""
    # Initialize session state
    if 'generation_requested' not in st.session_state:
        st.session_state.generation_requested = False

    # Header section
    render_header()

    # Input section
    module, scenario_type, acceptance_criteria = input_section()

    if st.button("Generate Test Cases", key="generate_button"):
        st.session_state.generation_requested = True
        st.session_state.module = module
        st.session_state.scenario_type = scenario_type
        st.session_state.acceptance_criteria = acceptance_criteria

    # Generation section
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

                    # Debug raw test cases for troubleshooting
                    st.write("### Debug: Raw Generated Test Cases")
                    st.code(test_cases, language="text")

                    # Parse and export section
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

from dotenv import load_dotenv
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

# Initialize the language model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_output_tokens=4096,
)

# Define the prompt template for test case generation
prompt_template = PromptTemplate(
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


def main():
    # Header with gradient background
    st.markdown("""
        <h1>🧪Test Case Generator</h1>
        <p style='text-align: center; font-size: 1.2em; color: #666; margin-bottom: 2rem;'>
            Generate comprehensive test cases with intelligent scenario coverage
        </p>
    """, unsafe_allow_html=True)

    # Create three columns for inputs
    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown("##### 📦 Module Information")
            module = st.text_input(
                "Module Name",
                placeholder="Enter module name...",
                help="Enter the name of the module you want to test"
            )

        with col2:
            st.markdown("##### 🎯 Test Coverage")
            scenario_type = st.selectbox(
                "Scenario Type",
                ["All Scenarios", "Positive Scenarios", "Negative Scenarios"],
                help="Select the type of test scenarios to generate"
            )

        with col3:
            st.markdown("##### ✅ Requirements")
            acceptance_criteria = st.text_area(
                "Acceptance Criteria",
                placeholder="Enter acceptance criteria...",
                help="Enter the acceptance criteria for the module",
                height=100
            )

    # Generate test cases and allow export
    if st.button("Generate Test Cases"):
        if module and acceptance_criteria:
            with st.spinner("Generating test cases..."):
                # Generate the response using the LLM
                prompt = prompt_template.format(
                    Module=module,
                    AcceptanceCriteria=acceptance_criteria,
                    ScenarioType=scenario_type
                )
                response = llm.invoke(prompt)

                if response and hasattr(response, "content"):
                    st.write("### Generated Test Cases:")
                    test_cases = response.content
                    st.write(test_cases)

        else:
            st.warning("Please fill in all required fields.")


if __name__ == "__main__":
    main()

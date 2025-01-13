import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

@st.cache_resource
def initialize_llm():
    """Lazy load the LLM only when needed"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
        max_output_tokens=4096,
    )

@st.cache_data
def get_prompt_template():
    """Cache the prompt template"""
    from langchain.prompts import PromptTemplate
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
            "Steps: [Numbered steps to execute]\n"
            "Expected Results: [Expected outcome]\n\n"
            "Generate multiple test cases, with each separated by a blank line."
        )
    )

def generate_test_cases(module, acceptance_criteria, scenario_type):
    """Generate test cases only when the button is clicked"""
    llm = initialize_llm()
    prompt_template = get_prompt_template()
    
    prompt = prompt_template.format(
        Module=module,
        AcceptanceCriteria=acceptance_criteria,
        ScenarioType=scenario_type
    )
    return llm.invoke(prompt)

def main():
    st.title("🧪 Test Case Generator")
    
    # Simple input fields
    module = st.text_input("Module Name", placeholder="Enter module name...")
    scenario_type = st.selectbox(
        "Scenario Type",
        ["All Scenarios", "Positive Scenarios", "Negative Scenarios"]
    )
    acceptance_criteria = st.text_area(
        "Acceptance Criteria",
        placeholder="Enter acceptance criteria..."
    )

    # Only generate test cases when the button is clicked
    if st.button("Generate Test Cases"):
        if module and acceptance_criteria:
            with st.spinner("Generating test cases..."):
                try:
                    response = generate_test_cases(module, acceptance_criteria, scenario_type)
                    if response and hasattr(response, "content"):
                        st.write("### Generated Test Cases:")
                        st.write(response.content)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.error("Please check your Google API key and internet connection.")
        else:
            st.warning("Please fill in all required fields.")

if __name__ == "__main__":
    main()

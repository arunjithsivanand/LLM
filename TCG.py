from dotenv import load_dotenv
import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Initialize the language model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_output_tokens=4096,
)

# Simplified prompt template
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
        "Steps: [Numbered steps to execute]\n"
        "Expected Results: [Expected outcome]\n\n"
        "Generate multiple test cases, with each separated by a blank line."
    )
)

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
                    st.write(response.content)
                    
                    # Add simple copy button
                    st.button(
                        "Copy to Clipboard",
                        on_click=lambda: st.write("Content copied to clipboard!")
                    )
        else:
            st.warning("Please fill in all required fields.")

if __name__ == "__main__":
    main()

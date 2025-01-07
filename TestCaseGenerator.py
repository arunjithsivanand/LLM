from dotenv import load_dotenv
import pandas as pd
import xlsxwriter
import openpyxl
from io import BytesIO
import re

load_dotenv()

import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

st.set_page_config(
    page_title="Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def parse_test_cases(text):
    """Parse the generated test cases into a structured format"""
    test_cases = []
    current_case = {}

    # Split the text into lines
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            if current_case:
                test_cases.append(current_case)
                current_case = {}
            continue

        # Check for Test Case ID
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

    # Add the last test case if exists
    if current_case:
        test_cases.append(current_case)

    return test_cases


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
        <h1>🧪 Advanced Test Case Generator</h1>
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

                    # Parse the test cases into structured format
                    parsed_test_cases = parse_test_cases(test_cases)

                    if parsed_test_cases:
                        # Convert to DataFrame
                        df = pd.DataFrame(parsed_test_cases)

                        # Convert DataFrame to Excel
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name="Test Cases")

                            # Get the workbook and worksheet objects
                            workbook = writer.book
                            worksheet = writer.sheets["Test Cases"]

                            # Add some formatting
                            header_format = workbook.add_format({
                                'bold': True,
                                'fg_color': '#D7E4BC',
                                'border': 1
                            })

                            # Write the header with the format
                            for col_num, value in enumerate(df.columns.values):
                                worksheet.write(0, col_num, value, header_format)
                                worksheet.set_column(col_num, col_num, 20)  # Set column width

                        # Get the Excel file data
                        excel_data = output.getvalue()

                        # Provide download button for Excel file
                        st.download_button(
                            label="Download Test Cases as Excel",
                            data=excel_data,
                            file_name=f"{module}_test_cases.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    else:
                        st.error("Failed to parse test cases. Please check the generated format.")
        else:
            st.warning("Please fill in all required fields.")


if __name__ == "__main__":
    main()

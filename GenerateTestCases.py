from dotenv import load_dotenv
import pandas as pd
from io import StringIO
import os
import streamlit as st
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

st.set_page_config(
    page_title="Test Case Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize model with simpler configuration
@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-pro')

def parse_test_cases(text):
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
                'tag': 'Tags'
            }
            
            for k, v in key_map.items():
                if k in key.lower():
                    current_case[v] = value
                    break

    if current_case:
        test_cases.append(current_case)
    return test_cases

def main():
    st.markdown("""
        <h1>🧪 Quick Test Case Generator</h1>
    """, unsafe_allow_html=True)

    # Compact input form
    module = st.text_input("Module Name", key="module_input")
    
    # Two-column layout for criteria and type
    col1, col2 = st.columns([3, 1])
    
    with col1:
        criteria = st.text_area(
            "Acceptance Criteria (required)",
            height=100,
            key="criteria_input",
            help="Enter the requirements or user story"
        )
    
    with col2:
        test_type = st.radio(
            "Test Type",
            ["Positive", "Negative"],
            index=0,
            key="test_type"
        )

    # Initialize session state
    if 'test_cases' not in st.session_state:
        st.session_state.test_cases = None
        st.session_state.df = None

    # Generate button
    if st.button("Generate Test Cases", type="primary", use_container_width=True):
        if not module or not criteria:
            st.warning("Please fill in both Module Name and Acceptance Criteria.")
            return

        try:
            model = get_model()
            
            # Simple prompt for faster generation
            prompt = f"""
Create 3 quick {test_type.lower()} test cases for:
Module: {module}
Requirements: {criteria}

Format (keep it brief):
Test Case ID: TC-XX
Description: brief description
Pre-conditions: key conditions
Steps: main steps
Expected Results: expected outcome
Tags: relevant tags

Skip post-conditions. Keep each test case short and focused."""

            # Show immediate feedback
            with st.status("Generating test cases...", expanded=True) as status:
                st.write("🔄 Starting generation...")
                
                # Generate test cases
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        top_p=0.8,
                        top_k=20,
                        max_output_tokens=1024
                    )
                )
                
                if response:
                    test_cases = response.text
                    st.session_state.test_cases = test_cases
                    
                    # Parse test cases
                    st.write("✨ Parsing results...")
                    parsed_cases = parse_test_cases(test_cases)
                    
                    if parsed_cases:
                        df = pd.DataFrame(parsed_cases)
                        st.session_state.df = df
                        status.update(label="✅ Generation Complete!", state="complete")
                    else:
                        status.update(label="❌ Parsing failed", state="error")
                else:
                    status.update(label="❌ Generation failed", state="error")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return

    # Show results if available
    if st.session_state.test_cases:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.expander("View Generated Test Cases", expanded=True):
                st.text_area(
                    "",
                    value=st.session_state.test_cases,
                    height=200,
                    disabled=True
                )
        
        with col2:
            if st.session_state.df is not None:
                # Create download button
                csv = st.session_state.df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"{module}_test_cases.csv",
                    "text/csv",
                    use_container_width=True
                )
                
                st.success(f"Generated {len(st.session_state.df)} test cases")

if __name__ == "__main__":
    main()

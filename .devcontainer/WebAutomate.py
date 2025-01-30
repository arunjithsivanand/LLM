import streamlit as st
import asyncio
from typing import List, Optional
from pydantic import BaseModel
import os
from browser_use import Agent, Controller
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize session state
if 'prompts' not in st.session_state:
    st.session_state.prompts = []

class TestConfig(BaseModel):
    url: str
    username: str
    password: str
    prompts: List[str]

async def run_browser_test(config: TestConfig) -> str:
    task = f"""Navigate to {config.url} and perform comprehensive end-to-end testing:
    1. Initial Page Load Test:
    - Verify all elements are properly loaded
    - Check responsiveness of the login page
    - Validate all links are working
    2. Login Process:
    - Click on the Sign In button
    - Enter email: {config.username}
    - Enter password: {config.password}
    - Click the login button
    - Verify successful login
    3. Post-Login Testing:
    - Verify successful navigation to dashboard
    - Test the main navigation menu
    - Check all visible buttons and links
    - Verify user profile information
    4. Feature Testing:
    - Test the search functionality if available
    - Test the add functionality and validate the insertion of the new record in the UI 
    - Check any filters or sorting options
    - Test data display in tables or lists
    - Verify any CRUD operations available
    5. Responsive Testing:
    - Check layout on different viewport sizes
    - Verify menu behavior
    - Test button and input field responsiveness
    6. Error Handling:
    - Test form validations
    - Check error messages
    - Verify proper handling of invalid inputs
    7. Performance Checks:
    - Monitor page load times
    - Check response time for actions
    - Verify smooth transitions
    
    Additional Test Cases:
    {chr(10).join([f"- {prompt}" for prompt in config.prompts])}
    
    Document all findings including:
    - Functionality issues
    - UI/UX problems
    - Performance concerns
    - Error handling effectiveness
    - Navigation flow issues
    - Any bugs or unexpected behavior
    """
    
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp')
    agent = Agent(task=task, llm=llm)
    history = await agent.run()
    return history.final_result()

def main():
    st.set_page_config(page_title="Website Testing Tool", layout="wide")
    
    # Apply custom styling
    st.markdown("""
        <style>
        .stTextInput > div > div > input {
            background-color: white;
        }
        .stTextArea > div > div > textarea {
            background-color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🌐 Website Testing Tool")
    
    # Create three columns for the form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Test Configuration")
        url = st.text_input("Website URL", placeholder="https://example.com")
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password")
        
        # Prompt input and management
        new_prompt = st.text_area("Add Testing Prompt", placeholder="Enter additional test cases or requirements...")
        if st.button("Add Prompt"):
            if new_prompt.strip():
                st.session_state.prompts.append(new_prompt.strip())
                st.success("Prompt added successfully!")
    
    with col2:
        st.subheader("Current Prompts")
        if st.session_state.prompts:
            for i, prompt in enumerate(st.session_state.prompts):
                col_prompt, col_delete = st.columns([4, 1])
                with col_prompt:
                    st.text_area(f"Prompt {i+1}", value=prompt, height=100, key=f"prompt_{i}", disabled=True)
                with col_delete:
                    if st.button("🗑️", key=f"delete_{i}"):
                        st.session_state.prompts.pop(i)
                        st.rerun()
        else:
            st.info("No prompts added yet.")
    
    # Start Testing button
    if st.button("Start Testing", type="primary", use_container_width=True):
        if not (url and username and password):
            st.error("Please fill in all required fields (URL, Username, and Password)")
            return
            
        try:
            config = TestConfig(
                url=url,
                username=username,
                password=password,
                prompts=st.session_state.prompts
            )
            
            with st.spinner("Running tests..."):
                # Create a new event loop and run the test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(run_browser_test(config))
                finally:
                    loop.close()
                
                # Display results
                st.subheader("Test Results")
                st.markdown(result)
                
                # Option to download results
                st.download_button(
                    label="Download Results",
                    data=result,
                    file_name="test_results.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

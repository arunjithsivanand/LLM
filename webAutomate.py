import streamlit as st
import asyncio
from typing import List, Optional
from pydantic import BaseModel
import os
from browser_use import Agent, Controller
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")


class TestCase(BaseModel):
    url: str
    email: str
    password: str
    custom_tests: List[str] = []


def generate_test_task(test_case: TestCase) -> str:
    base_task = f"""Navigate to {test_case.url} and perform comprehensive end-to-end testing:
    1. Initial Page Load Test:
    - Verify all elements are properly loaded
    - Check responsiveness of the login page
    - Validate all links are working

    2. Login Process:
    - Click on the Sign In button
    - Enter email: {test_case.email}
    - Enter password: {test_case.password}
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
    - Verify smooth transitions"""

    if test_case.custom_tests:
        base_task += "\n\n8. Custom Test Cases:"
        for test in test_case.custom_tests:
            base_task += f"\n- {test}"

    base_task += """\n\nDocument all findings including:
    - Functionality issues
    - UI/UX problems
    - Performance concerns
    - Error handling effectiveness
    - Navigation flow issues
    - Any bugs or unexpected behavior"""

    return base_task


async def run_test(test_case: TestCase) -> str:
    task = generate_test_task(test_case)
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp')
    agent = Agent(task=task, llm=llm)

    try:
        history = await agent.run()
        result = history.final_result()
        if not result:
            raise ValueError("No result returned from the agent.")
        return result
    except Exception as e:
        print(f"Error during test execution: {e}")
        return None


def run_test_sync(test_case: TestCase) -> str:
    """Wrapper to run the async function synchronously"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(run_test(test_case))


def main():
    st.set_page_config(
        page_title="Web Testing Tool",
        page_icon="🌐",
        layout="wide"
    )

    st.title("🌐 Web Testing Tool")

    # Initialize session state for custom tests
    if 'custom_tests' not in st.session_state:
        st.session_state.custom_tests = []

    # Create two columns for the main layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Test Configuration")

        # Main form inputs
        url = st.text_input(
            "Website URL",
            value="https://padev.core42.protal.biz/chat",
            help="Enter the website URL to test"
        )

        email = st.text_input(
            "Email",
            value="prod_data@dagster.com",
            help="Enter the login email"
        )

        password = st.text_input(
            "Password",
            value="gTA%2*pYET7FJ^3t",
            type="password",
            help="Enter the login password"
        )

        # Custom test case input
        st.subheader("Add Custom Test Cases")
        new_test = st.text_area(
            "Custom Test Case",
            placeholder="Enter a custom test case to add to the testing suite..."
        )

        if st.button("Add Test Case"):
            if new_test.strip():
                st.session_state.custom_tests.append(new_test.strip())
                st.success("Test case added!")

    with col2:
        st.subheader("Current Custom Test Cases")
        if st.session_state.custom_tests:
            for i, test in enumerate(st.session_state.custom_tests):
                col_test, col_delete = st.columns([4, 1])
                with col_test:
                    st.text_area(
                        f"Test #{i + 1}",
                        value=test,
                        disabled=True,
                        height=100,
                        key=f"test_{i}"
                    )
                with col_delete:
                    if st.button("🗑️", key=f"delete_{i}"):
                        st.session_state.custom_tests.pop(i)
                        st.rerun()
        else:
            st.info("No custom test cases added yet.")

    # Run tests button
    if st.button("Run Tests", type="primary", use_container_width=True):
        if not all([url, email, password]):
            st.error("Please fill in all required fields!")
            return

        try:
            test_case = TestCase(
                url=url,
                email=email,
                password=password,
                custom_tests=st.session_state.custom_tests
            )

            with st.spinner("Running tests... This may take a few minutes."):
                # Progress bar
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.1)
                    progress_bar.progress(i + 1)

                # Run the test synchronously
                result = run_test_sync(test_case)

                if result is None:
                    st.error("Test failed to produce a valid result.")
                    return

                st.success("Testing completed!")
                st.subheader("Test Results")

                # Create tabs for different result views
                tab1, tab2 = st.tabs(["📝 Details", "📊 Summary"])

                with tab1:
                    st.markdown(result)

                with tab2:
                    # Extract key findings
                    findings = result.split('\n')
                    issues = [f for f in findings if any(k in f.lower() for k in ['issue', 'problem', 'bug', 'error'])]

                    st.markdown("### Key Findings")
                    for issue in issues:
                        st.markdown(f"- {issue}")

                # Download button for results
                st.download_button(
                    label="Download Results",
                    data=result,
                    file_name="test_results.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)


if __name__ == "__main__":
    main()

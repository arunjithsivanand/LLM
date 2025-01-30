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

def main():
    st.set_page_config(
        page_title="Web Testing Tool",
        page_icon="🌐",
        layout="wide"
    )

    st.title("🌐 Web Testing Tool")

    # Existing code ...

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

                # Run the test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(run_test(test_case))
                finally:
                    loop.close()

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


import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Retrieve the API key
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
if not GOOGLE_API_KEY:
    st.error("Google API key is missing. Please set it in the .env file.")
    st.stop()

# Initialize Streamlit App
st.title("Travel Guide")

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    api_key=GOOGLE_API_KEY,
    temperature=0,
    max_output_tokens=4096,
)

# Define the Prompt Template
prompt_template = PromptTemplate(
    input_variables=["city", "month", "language", "budget"],
    template="""Welcome to the {city} travel guide!
    If you’re visiting in {month}, here is what you can do:
    1. Must-Visit attractions
    2. Local Cuisine you must try.
    3. Useful phrases in {language}
    4. Tips for traveling on a {budget} budget

Enjoy your trip!!"""
)

# User Inputs
city = st.text_input("Enter the city")
month = st.text_input("Enter the month of travel")
language = st.text_input("Enter the language")
budget = st.selectbox("Travel Budget", ["High", "Mid", "Low"])
generate_button = st.button("Generate Travel Guide")

# Generate Travel Guide
if generate_button:
    if city and month and language and budget:
        try:
            response = llm.invoke(
                prompt_template.format(city=city, month=month, language=language, budget=budget)
            )
            st.write("### Your Travel Guide:")
            st.write(response.content)
        except Exception as e:
            st.error(f"An error occurred: {e}")

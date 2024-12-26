
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

# Define the prompt template
prompt_template = PromptTemplate(
    input_variables=["city", "month", "language", "budget"],
    template=(
        "Welcome to the {city} travel guide!\n"
        "If you’re visiting in {month}, here is what you can do:\n"
        "1. Must-visit attractions.\n"
        "2. Local cuisine you must try.\n"
        "3. Useful phrases in {language}.\n"
        "4. Tips for traveling on a {budget} budget.\n\n"
        "Enjoy your trip!"
    ),
)

# User inputs
city = st.text_input("Enter the country or city:")
month = st.text_input("Enter the month of travel:")
month = st.selectbox("Month:", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
language = st.text_input("Enter the language:", ["English"])
budget = st.selectbox("Travel Budget:", ["High", "Mid", "Low"])

# Submit button logic
if st.button("Submit"):
    if city and month and language and budget:
        # Generate the response using the LLM
        prompt = prompt_template.format(
            city=city, month=month, language=language, budget=budget
        )
        response = llm.invoke(prompt)
        if response and hasattr(response, "content"):
            st.write(response.content)
        else:
            st.error("Failed to fetch a response. Please check your API key or inputs.")
    else:
        st.warning("Please fill in all the fields before submitting.")

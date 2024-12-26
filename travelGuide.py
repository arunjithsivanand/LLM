from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
from langchain_google_genai import  ChatGoogleGenerativeAI
import base64
import os


def encode_image(image_file):
    # with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that can describe images."),
        (
            "human",
            [
                {"type": "text", "text": "{input}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,""{image}",
                        "detail": "low",
                    },
                },
            ],
        ),
    ]
)

chain = prompt | llm

uploaded_file = st.file_uploader("Upload your image", type = ["jpg","png"])
question =st.text_input("Enter the Question")
if question:
    image = encode_image(uploaded_file)
    response = chain.invoke({"input": question, "image": image})
    # Corrected line: Use st.write to display the response content
    st.write(response.content)

from typing import List, Optional
from pydantic import BaseModel
import os
from playwright.sync_api import sync_playwright
from browser_use import Agent, Controller
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import asyncio
import json
load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
print(GOOGLE_API_KEY)
async def browser_search() -> str:
   task = f"""Navigate to and perform comprehensive end-to-end testing:
   1. Initial Page Load Test:
   - Verify all elements are properly loaded
   - Check responsiveness of the login page
   - Validate all links are working
   2. Login Process:
   - Click on the Sign In button
   - Enter email: 
   - Enter password: 
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
   Document all findings including:
   - Functionality issues
   - UI/UX problems
   - Performance concerns
   - Error handling effectiveness
   - Navigation flow issues
   - Any bugs or unexpected behavior
   """
   llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp')
   # agent = Agent(task=task, llm=ChatOpenAI(model="gpt-4o-mini"))


   # llm = ChatGoogleGenerativeAI(model="gemini-pro")



   agent = Agent(task=task, llm=llm)

   history = await agent.run()
   return history.final_result()

if __name__ == "__main__":
   async def test():
       result = await browser_search()
       print("\nFinal Result:")
       print(result)
   loop = asyncio.new_event_loop()
   asyncio.set_event_loop(loop)
   try:
       loop.run_until_complete(test())
   finally:
       loop.close()

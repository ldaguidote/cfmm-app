import openai
import requests
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get the API key from the .env file
api_key = os.getenv("OPENAI_API_KEY")

# Set up the OpenAI API key
openai.api_key = api_key
import os
import time
import openai
import pyperclip
import random
from utils import *
from dotenv import load_dotenv

def call_chatgpt(name,prompt,log_dir, model="gpt-3.5-turbo",temperature=0.7):
    """
    Call the ChatGPT API with a given prompt.
    """
    try:
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')

        response = openai.ChatCompletion.create(
            model=model,
        messages=[{
            "role": "user",
            "content": prompt
        }],
        temperature=temperature,
        )

        response_text= response.choices[0].message['content']
        if response_text == prompt:
            return call_chatgpt(name, prompt, log_dir, model, temperature)
        else:
            return write_LLMlog(name, prompt, response_text, log_dir)
    except Exception as e:
        return f"An error occurred: {e}"
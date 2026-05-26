
from groq import Groq
from app.config import settings

import os

client = Groq(api_key=settings.GROQ_API_KEY)

def generate_sql(prompt: str):
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant",   # llama-3.3-70b-versatile # llama-3.1-8b-instant

        temperature = 0,
        max_tokens = 500,
    )

    return response.choices[0].message.content.strip()
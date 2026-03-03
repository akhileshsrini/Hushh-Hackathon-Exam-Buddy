import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "llama-3.1-8b-instant"


def generate_summary(content):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": f"""
You are an academic assistant.
Create a structured summary with headings and bullet points.

Content:
{content}
"""
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


def generate_quiz(content):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a JSON generator. You ONLY return valid JSON. No markdown. No explanation."
            },
            {
                "role": "user",
                "content": f"""
Generate 5 multiple choice questions from the content.

Return ONLY a valid JSON array.
Do NOT wrap in markdown.
Do NOT add ```json.
Do NOT explain.

Format:

[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Exact correct option text"
  }}
]

Content:
{content}
"""
            }
        ],
        temperature=0.2
    )
    print(response.choices[0].message.content.strip())

    return response.choices[0].message.content.strip()
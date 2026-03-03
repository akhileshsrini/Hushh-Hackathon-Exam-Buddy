from flask import Flask, request, jsonify
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from groq import Groq

# ------------------------
# CONFIG
# ------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")
client = Groq(api_key="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")  

texts = []
index = None


# ------------------------
# PDF FUNCTIONS
# ------------------------

def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text


def chunk_text(text, size=500):
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]


def build_vector_db(text_chunks):
    emb = model.encode(text_chunks)
    dim = emb.shape[1]
    idx = faiss.IndexFlatL2(dim)
    idx.add(np.array(emb).astype("float32"))
    return idx


# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def home():
    return jsonify({"message": "Kai Exam Buddy Backend Running 🚀"})


# 1️⃣ Upload PDF & Build Knowledge Base
@app.route("/upload", methods=["POST"])
def upload():
    global texts, index

    if "pdf" not in request.files:
        return jsonify({"error": "No PDF uploaded"}), 400

    file = request.files["pdf"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    raw_text = read_pdf(path)
    texts = chunk_text(raw_text)
    index = build_vector_db(texts)

    return jsonify({
        "message": "PDF processed successfully ✅",
        "filename": file.filename,
        "chunks_created": len(texts)
    })


# 2️⃣ Generate Summary
@app.route("/summarize", methods=["POST"])
def summarize():
    if not texts:
        return jsonify({"error": "No PDF uploaded yet"}), 400

    combined_text = " ".join(texts[:10])  # Limit to avoid token overload

    prompt = f"""
Summarize the following study material in a clear and structured way:
- Use headings
- Use bullet points
- Highlight key concepts in bold
- Keep it exam-focused

Content:
{combined_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700
    )

    summary = response.choices[0].message.content

    return jsonify({"summary": summary})


# 3️⃣ Generate Quiz
@app.route("/generate-quiz", methods=["POST"])
def generate_quiz():
    if not texts:
        return jsonify({"error": "No PDF uploaded yet"}), 400

    combined_text = " ".join(texts[:10])

    prompt = f"""
Create 10 multiple-choice quiz questions from the following study material.

Format:
1. Question?
   A)
   B)
   C)
   D)
   Answer: X

Make questions conceptual and exam-level.

Content:
{combined_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900
    )

    quiz = response.choices[0].message.content

    return jsonify({"quiz": quiz})


# ------------------------
# RUN SERVER
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)
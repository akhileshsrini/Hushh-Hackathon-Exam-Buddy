import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ---------------- USER ----------------
def create_or_get_user(name, email):
    user_ref = db.collection("users").document(email)
    doc = user_ref.get()

    if not doc.exists:
        user_ref.set({
            "name": name,
            "email": email,
            "created_at": datetime.utcnow()
        })

    return user_ref


# ---------------- CHAT ----------------
def create_chat(user_email, content):
    chat_id = str(uuid.uuid4())

    # Auto title from first words
    words = content.strip().split()
    title = " ".join(words[:6])
    if len(words) > 6:
        title += "..."

    db.collection("users").document(user_email)\
        .collection("chats").document(chat_id).set({
            "content": content,
            "title": title,
            "summary": "",
            "quiz": ""
        })

    return chat_id

def get_user_chats(user_email):
    chats_ref = db.collection("users").document(user_email).collection("chats").stream()

    chats = []

    for chat in chats_ref:
        data = chat.to_dict()
        chats.append({
            "chat_id": chat.id,
            "title": data.get("title", "Untitled")
        })

    return chats

def get_chat(email, chat_id):
    doc = db.collection("users") \
            .document(email) \
            .collection("chats") \
            .document(chat_id) \
            .get()

    return doc.to_dict()


def update_summary(email, chat_id, summary):
    db.collection("users") \
      .document(email) \
      .collection("chats") \
      .document(chat_id) \
      .update({"summary": summary})


def update_quiz(email, chat_id, quiz):
    db.collection("users") \
      .document(email) \
      .collection("chats") \
      .document(chat_id) \
      .update({"quiz": quiz})
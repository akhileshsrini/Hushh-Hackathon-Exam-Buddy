import streamlit as st
from services.firebase_service import (
    create_chat,
    get_user_chats,
    get_chat,
    update_summary,
    update_quiz,
    create_or_get_user
)
from services.groq_service import generate_summary, generate_quiz
from services.file_processor import extract_text_from_pdf, extract_text_from_ppt
import re
import json

# ---------------- SESSION INIT ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "page" not in st.session_state:
    st.session_state.page = "summary"

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0

if "score" not in st.session_state:
    st.session_state.score = 0

# ---------------- LOGIN ----------------
if st.session_state.user is None:

    st.title("Hushh Kai - Login")

    name = st.text_input("Enter your Name")
    email = st.text_input("Enter your Email")

    if st.button("Continue"):
        if name and email:

            create_or_get_user(name, email)

            st.session_state.user = {
                "name": name,
                "email": email
            }

            st.rerun()

# ---------------- MAIN APP ----------------
else:

    user_email = st.session_state.user["email"]
    user_name = st.session_state.user["name"]

    # -------- SIDEBAR --------
    with st.sidebar:

        # New Chat
        if st.button("+ New Chat", use_container_width=True):
            st.session_state.chat_id = None
            st.rerun()

        st.divider()
        st.subheader("Your Chats")

        chats = get_user_chats(user_email)

        if chats:
            for chat in chats:

                chat_id = str(chat.get("chat_id", ""))
                title = str(chat.get("title", "Untitled"))

                is_active = chat_id == st.session_state.chat_id
                button_type = "primary" if is_active else "secondary"

                if st.button(
                    title,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                    type=button_type
                ):
                    st.session_state.chat_id = chat_id
                    st.rerun()
        else:
            st.caption("No chats yet")

        st.divider()

        # Logout at bottom
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.chat_id = None
            st.rerun()

    # -------- MAIN CONTENT --------
    if st.session_state.chat_id is None:

        uploaded_file = st.file_uploader("Upload PDF or PPTX", type=["pdf", "pptx"])
        typed_notes = st.text_area("Or type notes")

        if st.button("Submit Notes"):

            content = ""

            if uploaded_file:
                file_type = uploaded_file.name.split(".")[-1].lower()

                if file_type == "pdf":
                    content = extract_text_from_pdf(uploaded_file)

                elif file_type == "pptx":
                    content = extract_text_from_ppt(uploaded_file)

            if typed_notes:
                content += "\n" + typed_notes

            if content.strip():
                chat_id = create_chat(user_email, content)
                st.session_state.chat_id = chat_id
                st.success("Chat created!")
                st.rerun()
    else:
        chat_data = get_chat(user_email, st.session_state.chat_id)

        # -------- SUMMARY PAGE --------
        if st.session_state.page == "summary":

            if st.button("Generate Quiz"):
                with st.spinner("Generating quiz..."):
                    quiz_raw = generate_quiz(chat_data["content"])

                try:
                    # Extract JSON array safely using regex
                    json_match = re.search(r"\[.*\]", quiz_raw, re.DOTALL)

                    if not json_match:
                        raise ValueError("No JSON array found")

                    quiz_json = json.loads(json_match.group())

                    st.session_state.quiz_data = quiz_json
                    st.session_state.quiz_index = 0
                    st.session_state.score = 0
                    st.session_state.page = "quiz"
                    st.rerun()

                except Exception as e:
                    st.error("Quiz parsing failed. See raw output below:")
                    st.code(quiz_raw)

            if not chat_data.get("summary"):
                with st.spinner("Generating summary..."):
                    summary = generate_summary(chat_data["content"])
                    update_summary(user_email, st.session_state.chat_id, summary)
                st.rerun()

            chat_data = get_chat(user_email, st.session_state.chat_id)

            if chat_data.get("summary"):
                st.markdown("## Summary")
                st.write(chat_data["summary"])

        # -------- QUIZ PAGE --------
        elif st.session_state.page == "quiz":
            st.title("Quiz")

            # Back button
            if st.button("⬅ Back to Summary"):
                st.session_state.page = "summary"
                st.session_state.quiz_data = None
                st.session_state.quiz_index = 0
                st.session_state.score = 0
                st.rerun()

            st.divider()

            questions = st.session_state.quiz_data
            index = st.session_state.quiz_index

            if index < len(questions):

                q = questions[index]

                st.markdown(f"### Question {index + 1} of {len(questions)}")
                st.write(q["question"])

                selected = st.radio(
                    "Choose an answer:",
                    q["options"],
                    key=f"question_{index}"
                )

                if st.button("Next"):

                    if selected == q["answer"]:
                        st.session_state.score += 1

                    st.session_state.quiz_index += 1
                    st.rerun()

            else:
                st.success("Quiz Completed 🎉")
                st.markdown(f"## Final Score: {st.session_state.score} / {len(questions)}")

                if st.button("Restart Quiz"):
                    st.session_state.quiz_index = 0
                    st.session_state.score = 0
                    st.rerun()
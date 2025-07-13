"""
Smart Assistant – Gemini Edition
--------------------------------
Streamlit app powered by Google Gemini for:
• Uploading PDF or TXT
• Auto-summarizing content (≤150 words)
• Free-form Q&A on uploaded document
• Challenge Me (objective & subjective quiz)

Requires:
  - GOOGLE_API_KEY in .env or environment
  - pip install -r requirements.txt
"""

import os
import streamlit as st
from dotenv import load_dotenv

# ────────────────────────────────
# 🔧 Load Gemini API key
# ────────────────────────────────
load_dotenv()
gemini_key = os.getenv("GOOGLE_API_KEY")

if not gemini_key:
    st.error("❌ GOOGLE_API_KEY is not set. Add it to .env or environment.")
    st.stop()

# ────────────────────────────────
# 📦 Local module imports
# ────────────────────────────────
from backend.file_parser import extract_text
from backend.summarizer import summarise_document
from backend.qa_engine import answer_question
from backend.challenge import (
    generate_quiz,
    evaluate_answer,
    generate_subjective_questions,
)

# ────────────────────────────────
# 🎛️ Streamlit UI setup
# ────────────────────────────────
st.set_page_config("Smart Research Assistant (Gemini)", "🧠", layout="wide")
st.title("🧠 Gemini-Powered Research Assistant")

uploaded_file = st.file_uploader("📂 Upload a PDF or TXT file", type=["pdf", "txt"])

if uploaded_file:
    with st.spinner("📄 Extracting document text..."):
        doc_text = extract_text(uploaded_file)

    if not doc_text.strip():
        st.error("⚠️ No text extracted. Please upload a valid text-based document.")
        st.stop()

    st.session_state["doc_text"] = doc_text

    # ------------------- Summary ---------------------
    if "summary" not in st.session_state:
        with st.spinner("🧠 Generating summary using Gemini..."):
            try:
                st.session_state["summary"] = summarise_document(doc_text, gemini_key)
            except Exception as e:
                st.error(f"❌ Gemini API error during summarization: {e}")
                st.stop()

    st.subheader("📑 Document Summary (≤150 words)")
    st.write(st.session_state["summary"])

    # ------------------- Ask Anything ----------------
    st.markdown("---")
    st.subheader("💬 Ask Anything (Q&A Mode)")

    question = st.text_input("Ask a question based on the document:")
    if question:
        with st.spinner("🤖 Thinking with Gemini..."):
            try:
                result = answer_question(doc_text, question, gemini_key)
                st.markdown("**Answer:**")
                st.write(result["answer"])
                if result.get("justification"):
                    st.markdown("**Justification:**")
                    st.write(result["justification"])
            except Exception as e:
                st.error(f"❌ Gemini API error during Q&A: {e}")

    # ------------------- Challenge Me ----------------
    st.markdown("---")
    st.subheader("🧠 Challenge Me Mode")

    challenge_type = st.radio("Choose Challenge Type:", ["Objective (MCQs)", "Subjective (Descriptive)"])

    if st.button("🎯 Generate Challenge"):
        with st.spinner("🧠 Thinking with Gemini..."):
            try:
                if challenge_type.startswith("Objective"):
                    quiz = generate_quiz(doc_text, gemini_key)
                    st.session_state["quiz"] = quiz
                    st.session_state.pop("subjective", None)
                    st.success(f"✅ {len(quiz)} objective questions generated.")
                else:
                    subjective = generate_subjective_questions(doc_text, gemini_key)
                    st.session_state["subjective"] = subjective
                    st.session_state.pop("quiz", None)
                    st.success(f"✅ {len(subjective)} subjective questions generated.")
            except Exception as e:
                st.error(f"❌ Gemini API error during challenge generation: {e}")

    # ------------------- Display MCQ Quiz ----------------
    if "quiz" in st.session_state:
        st.markdown("### 📝 Objective Quiz")
        score = 0
        responses = []

        for i, q in enumerate(st.session_state["quiz"], start=1):
            st.markdown(f"**Q{i}. {q['question']}**")
            user_choice = st.radio(f"Options for Q{i}:", q["options"], key=f"q{i}")
            responses.append((user_choice, q["correct_option"]))
            st.markdown("---")

        if st.button("✅ Submit Objective Answers"):
            for idx, (user, correct) in enumerate(responses):
                if evaluate_answer(user, correct):
                    score += 1
            st.success(f"🎉 You scored {score}/{len(responses)}")

    # ------------------- Display Subjective Quiz ----------------
    if "subjective" in st.session_state:
        st.markdown("### 📝 Subjective Questions")
        for i, question in enumerate(st.session_state["subjective"], start=1):
            st.markdown(f"**Q{i}. {question}**")
            st.text_area("Your Answer:", key=f"subjective_q{i}")
else:
    st.info("📥 Please upload a PDF or TXT file to get started.")

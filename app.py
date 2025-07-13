import os
import streamlit as st
from dotenv import load_dotenv

# ───── Load Gemini API Key ─────
load_dotenv()
gemini_key = os.getenv("GOOGLE_API_KEY")

if not gemini_key:
    st.error("❌ GOOGLE_API_KEY is not set. Add it to .env or environment.")
    st.stop()

# ───── Local Module Imports ─────
from backend.file_parser import extract_text
from backend.summarizer import summarise_document
from backend.qa_engine import answer_question
from backend.challenge import (
    generate_quiz,
    evaluate_answer,
    generate_subjective_questions,
    evaluate_subjective
)

# ───── Streamlit UI Setup ─────
st.set_page_config("Smart Research Assistant (Gemini)", "🧠", layout="wide")
st.title("🧠 Smart Assistant for Research Summarization")

uploaded_file = st.file_uploader("📂 Upload a PDF or TXT file", type=["pdf", "txt"])

if uploaded_file:
    with st.spinner("📄 Extracting document text..."):
        doc_text = extract_text(uploaded_file)

    if not doc_text.strip():
        st.error("⚠️ No text extracted. Please upload a valid text-based document.")
        st.stop()

    st.session_state["doc_text"] = doc_text

    # ───── Summary ─────
    if "summary" not in st.session_state:
        with st.spinner("🧠 Generating summary..."):
            try:
                st.session_state["summary"] = summarise_document(doc_text, gemini_key)
            except Exception as e:
                st.error(f"❌ Summarization error: {e}")
                st.stop()

    st.subheader("📑 Document Summary")
    st.write(st.session_state["summary"])

    # ───── Q&A ─────
    st.markdown("---")
    st.subheader("💬 Ask Anything")

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
                st.error(f"❌ Q&A error: {e}")

    # ───── Challenge Me ─────
    st.markdown("---")
    st.subheader("🧠 Challenge Me Mode")

    challenge_type = st.radio("Choose Challenge Type:", ["Objective (MCQs)", "Subjective (Descriptive)"])

    if st.button("🎯 Generate Challenge"):
        with st.spinner("🧠 Generating challenge..."):
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
                st.error(f"❌ Challenge generation error: {e}")

    # ───── Objective Quiz ─────
    if "quiz" in st.session_state:
        st.markdown("### 📝 Objective Quiz")
        score = 0
        responses = []

        for i, q in enumerate(st.session_state["quiz"], start=1):
            st.markdown(f"**Q{i}. {q['question']}**")
            options = q["options"]
            user_choice = st.radio(f"Choose one:", options, key=f"q{i}")
            responses.append((user_choice, q["correct_option"]))
            st.markdown("---")

        if st.button("✅ Submit Objective Answers"):
            for idx, (user_ans, correct_letter) in enumerate(responses):
                if user_ans.strip().upper().startswith(correct_letter.upper()):
                    score += 1
            st.success(f"🎉 You scored {score}/{len(responses)}")

    # ───── Subjective Quiz ─────
    if "subjective" in st.session_state:
        st.markdown("### 📝 Subjective Questions")
        subjective_answers = []
        for i, question in enumerate(st.session_state["subjective"], start=1):
            st.markdown(f"**Q{i}. {question}**")
            user_ans = st.text_area("Your Answer:", key=f"subjective_q{i}")
            subjective_answers.append((question, user_ans))

        if st.button("✅ Submit Subjective Answers"):
            st.markdown("### 🧾 Feedback:")
            for i, (question, answer) in enumerate(subjective_answers, start=1):
                st.markdown(f"**Q{i}. {question}**")
                st.markdown(f"🖊️ Your Answer:\n{answer if answer.strip() else '_No answer provided._'}")
                with st.spinner("🔍 Evaluating..."):
                    feedback = evaluate_subjective(answer, question, gemini_key)
                st.markdown(f"📋 **Evaluation:** {feedback}")
                st.markdown("---")

else:
    st.info("📥 Please upload a PDF or TXT file to get started.")
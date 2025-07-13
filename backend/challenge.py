"""
Challenge Mode – Objective + Subjective Quiz Generator using Gemini
-------------------------------------------------------------------
This module supports:
1. Generating multiple-choice (objective) quiz questions
2. Generating descriptive (subjective) questions
3. Evaluating objective answers

Model: Gemini 1.5 Flash
"""

import google.generativeai as genai
import json
import re
from typing import List, Dict


def generate_quiz(document_text: str, api_key: str, num_questions: int = 5) -> List[Dict]:
    """
    Generate `num_questions` MCQs from the document.
    Each question format: {
        "question": "...",
        "options": ["A", "B", "C", "D"],
        "correct_option": "A"
    }
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

    prompt = (
        f"Read the following document and generate {num_questions} MCQs.\n"
        f"Each question should have 4 options and the correct answer clearly marked.\n"
        f"Return output strictly in this JSON format:\n\n"
        f"[{{\"question\": \"...\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct_option\": \"A\"}}, ...]\n\n"
        f"IMPORTANT: Return only valid JSON. No markdown. No explanation.\n\n"
        f"Document:\n{document_text[:10000]}"
    )

    try:
        response = model.generate_content(prompt)
        content = response.text.strip()

        # Attempt to parse directly as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Attempt to extract JSON if wrapped in extra text
            match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))

        raise RuntimeError("Gemini returned non-JSON or invalid quiz format.")

    except Exception as e:
        raise RuntimeError(f"Gemini quiz generation error: {e}")


def generate_subjective_questions(document_text: str, api_key: str, num_questions: int = 3) -> List[str]:
    """
    Generate `num_questions` subjective (descriptive) questions from the document.
    Returns a plain list of question strings.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

    prompt = (
        f"Based on the following document, generate {num_questions} short-answer or descriptive questions.\n"
        f"Return a numbered list of questions ONLY. Do not include answers, comments, or markdown formatting.\n\n"
        f"Document:\n{document_text[:10000]}"
    )

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Normalize and clean question list
        questions = [line.lstrip("1234567890). ").strip() for line in raw.splitlines() if line.strip()]
        return questions[:num_questions]

    except Exception as e:
        raise RuntimeError(f"Gemini subjective Q generation error: {e}")


def evaluate_answer(user_answer: str, correct_answer: str) -> bool:
    """
    Evaluate objective answers (MCQ).
    Returns True if user's answer matches the correct one.
    """
    return user_answer.strip().lower() == correct_answer.strip().lower()

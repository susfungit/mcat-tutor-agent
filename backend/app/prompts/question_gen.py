"""Question generation prompts for discrete and passage-based MCAT questions."""

DISCRETE_QUESTION_PROMPT = """\
Generate an MCAT-style discrete (standalone) question.

Section: {section}
Topic: {topic}
Subtopic: {subtopic}
Difficulty: {difficulty}/10

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
    "stem": "The question text",
    "options": {{
        "A": "First answer choice",
        "B": "Second answer choice",
        "C": "Third answer choice",
        "D": "Fourth answer choice"
    }},
    "correct_answer": "A",
    "explanation": {{
        "why_correct": "Explanation of why the correct answer is right",
        "why_wrong": {{
            "A": "Why A is wrong (omit if A is correct)",
            "B": "Why B is wrong (omit if B is correct)",
            "C": "Why C is wrong (omit if C is correct)",
            "D": "Why D is wrong (omit if D is correct)"
        }}
    }},
    "concepts_tested": ["concept1", "concept2"],
    "high_yield": true
}}

Requirements:
- Question should test understanding, not memorization
- All answer choices should be plausible
- Difficulty {difficulty}/10: {"basic recall" if difficulty <= 3 else "application and analysis" if difficulty <= 6 else "complex multi-step reasoning"}
- The explanation must be thorough enough to teach the concept
"""

PASSAGE_QUESTION_PROMPT = """\
Generate an MCAT-style passage-based question.

Section: {section}
Topic: {topic}
Subtopic: {subtopic}
Difficulty: {difficulty}/10

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
    "passage": "A 150-250 word scientific passage providing context for the question",
    "stem": "The question text referencing the passage",
    "options": {{
        "A": "First answer choice",
        "B": "Second answer choice",
        "C": "Third answer choice",
        "D": "Fourth answer choice"
    }},
    "correct_answer": "B",
    "explanation": {{
        "why_correct": "Explanation referencing the passage",
        "why_wrong": {{
            "A": "Why A is wrong",
            "B": "Why B is wrong (omit if B is correct)",
            "C": "Why C is wrong",
            "D": "Why D is wrong"
        }}
    }},
    "concepts_tested": ["concept1", "concept2"],
    "high_yield": true
}}

Requirements:
- The passage should present experimental data or a real-world scenario
- The question should require applying passage information to the topic
- All answer choices should be plausible
- Difficulty {difficulty}/10: {"basic recall" if difficulty <= 3 else "application and analysis" if difficulty <= 6 else "complex multi-step reasoning"}
"""

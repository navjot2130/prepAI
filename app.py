import streamlit as st
import requests

# ----------------------------
# 🔧 Configuration
# ----------------------------
TOTAL_QUESTIONS = 28
# ----------------------------

# Page configuration
st.set_page_config(page_title="AI Interview Question Generator", page_icon="💼", layout="wide")

# CSS styling with animated gradient
st.markdown("""
<style>
/* 🌈 Animated Gradient Background */
@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

body, [data-testid="stAppViewContainer"], .main {
    background: linear-gradient(270deg, #E6E6FA, #F8F8FF, #D8BFD8, #E0FFFF);
    background-size: 800% 800%;
    animation: gradientBG 20s ease infinite;
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-size: cover;
}

/* Subtle blur for glass effect */
[data-testid="stAppViewContainer"] > .main {
    backdrop-filter: blur(3px);
}

/* ===== Titles ===== */
.title-font { 
    font-family: "Segoe UI", Roboto, sans-serif; 
    font-size: 50px; 
    color: #4B0082; 
    font-weight: bold; 
    text-align: center; 
}
.subtitle { 
    font-size: 20px; 
    font-weight: bold; 
    color: #6A5ACD; 
    text-align: center; 
    margin-bottom: 30px; 
}

/* 💠 Original Indigo Button Style */
.stButton>button {
    background-color: #4B0082;
    color: white;
    font-size: 16px;
    font-weight: bold;
    border-radius: 8px;
    border: none;
    transition: all 0.3s ease-in-out;
    box-shadow: 0 0 0px rgba(75, 0, 130, 0);
}

.stButton>button:hover {
    background-color: #4B0082; 
    transform: scale(1.05);
    box-shadow: 0 0 15px rgba(75, 0, 130, 0.7);
}

.stButton>button:focus, .stButton>button:active {
    background-color: #5A00A5;
    box-shadow: 0 0 20px rgba(75, 0, 130, 0.9);
    outline: none;
}

/* ===== Question Cards ===== */
.question-card { 
    background-color: rgba(240,248,255,0.85); 
    border-left: 5px solid #6A5ACD; 
    padding: 15px; 
    margin-bottom: 10px; 
    border-radius: 10px; 
}
.answer { 
    background-color: rgba(230,230,250,0.85); 
    padding: 10px; 
    border-radius: 8px; 
    margin-top: 5px; 
}
.category-title { 
    color: #FFFFFF; 
    background-color: #4B0082; 
    font-weight: bold; 
    font-size: 28px; 
    padding: 10px; 
    border-radius: 8px; 
    margin-top: 20px; 
}

/* ===== Enhanced Input Labels ===== */
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
label[for^="widget"] {
    font-family: "Segoe UI", Roboto, sans-serif !important;
    font-weight: 800 !important;
    color: #000 !important;
    font-size: 20px !important;
    margin-bottom: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="title-font">💼 AI Interview Question Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Get instant, Role-specific Interview Questions 🤖</p>', unsafe_allow_html=True)

# Inputs
col1, col2 = st.columns([2, 1])
with col1:
    role = st.text_input("Enter the Job Role (e.g., Data Analyst, Web Developer)")
with col2:
    difficulty = st.selectbox("Select Difficulty", ["Beginner", "Intermediate", "Advanced"])

# Parser for Gemini output
def parse_gemini_output(text, total_questions):
    sections = ["Technical", "HR", "Scenario-Based", "Aptitude"]
    result = {sec: [] for sec in sections}
    current_section = None
    question, answer = "", ""

    for line in text.splitlines():
        line = line.strip()
        if not line: continue

        if any(line.lower().startswith(sec.lower()) for sec in sections):
            if question and current_section:
                result[current_section].append((question.strip(), answer.strip()))
            question, answer = "", ""
            for sec in sections:
                if line.lower().startswith(sec.lower()):
                    current_section = sec
                    break
            continue

        if line.lower().startswith("q") and ":" in line:
            if question and current_section:
                result[current_section].append((question.strip(), answer.strip()))
            question = line.split(":", 1)[1].strip()
            answer = ""
            continue

        if line.lower().startswith("answer") and ":" in line:
            answer = line.split(":", 1)[1].strip()
            continue

        if answer:
            answer += " " + line
        elif question:
            question += " " + line

    if question and current_section:
        result[current_section].append((question.strip(), answer.strip()))

    per_section = total_questions // len(sections)
    remainder = total_questions % len(sections)

    for i, sec in enumerate(sections):
        expected = per_section + (1 if i == len(sections) - 1 and remainder else 0)
        result[sec] = result[sec][:expected]
        while len(result[sec]) < expected:
            result[sec].append(("No question generated", "No answer generated"))

    return result

# Generate questions
if st.button("Generate Questions"):
    if not role:
        st.warning("Please enter a job role first.")
    else:
        with st.spinner("✨ Generating interview questions... Please wait."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/generate",
                    json={"role": role, "difficulty": difficulty, "total_questions": TOTAL_QUESTIONS}
                )
                data = response.json()

                if "questions" in data:
                    text = data["questions"]
                    st.success("✅ Interview Questions Generated!")

                    parsed = parse_gemini_output(text, TOTAL_QUESTIONS)

                    for section, qlist in parsed.items():
                        st.markdown(f'<p class="category-title">{section} Questions</p>', unsafe_allow_html=True)
                        for i, (q, a) in enumerate(qlist, 1):
                            st.markdown(
                                f'<div class="question-card"><b>Q{i}:</b> {q}'
                                f'<div class="answer"><b>Answer:</b> {a}</div></div>',
                                unsafe_allow_html=True
                            )

                    st.download_button(
                        label="📥 Download All Questions",
                        data=text,
                        file_name=f"{role}_interview_questions.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(data.get("error", "⚠️ Unknown error occurred"))

            except Exception as e:
                st.error(f"❌ Error: {e}")

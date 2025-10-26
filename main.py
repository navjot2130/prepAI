from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os
import math

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
genai.configure(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class InterviewRequest(BaseModel):
    role: str
    difficulty: str
    total_questions: int = 16  # default if not given


@app.post("/generate")
async def generate_questions(data: InterviewRequest):
    sections = ["Technical", "HR", "Scenario-Based", "Aptitude"]
    num_sections = len(sections)
    questions_per_section = data.total_questions // num_sections

    # If total questions is not divisible by 4, add remaining to last section
    remainder = data.total_questions % num_sections

    section_question_counts = [questions_per_section] * num_sections
    if remainder:
        section_question_counts[-1] += remainder

    # Construct prompt dynamically
    prompt_sections = []
    q_counter = 1
    for section_name, count in zip(sections, section_question_counts):
        section_block = f"\n{section_name} Questions:\n"
        for i in range(count):
            section_block += f"Q{q_counter}: <question>\nAnswer: <answer>\n"
            q_counter += 1
        prompt_sections.append(section_block)

    full_prompt = f"""
Generate exactly {data.total_questions} interview questions for the job role: {data.role}.
Difficulty level: {data.difficulty}.
Divide them evenly into 4 sections: Technical, HR, Scenario-Based, and Aptitude.
Each question must have a relevant and concise answer (2–3 lines max).
Avoid placeholders like 'No question generated'.

Format strictly like this:
{''.join(prompt_sections)}

Return only the text in this exact format. Do not include extra notes or explanations.
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(full_prompt)

        text = None
        if hasattr(response, "text") and response.text:
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            text = response.candidates[0].content.parts[0].text

        if text:
            # Safety fix: remove any incomplete lines at the end
            lines = text.strip().split("\n")
            cleaned_lines = []
            for line in lines:
                if "No question generated" not in line and "No answer generated" not in line:
                    cleaned_lines.append(line)
            final_text = "\n".join(cleaned_lines)
            return {"questions": final_text}

        else:
            return {"error": "No response from Gemini."}

    except Exception as e:
        return {"error": str(e)}

import os
import io
import time
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import PyPDF2

# Load environment variables from .env
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_text_from_pdf(pdf_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...)
):
    print("1. Extracting text from PDFs...")
    resume_text = extract_text_from_pdf(await resume.read())
    jd_text = extract_text_from_pdf(await job_description.read())
    print(f"2. Extracted {len(resume_text)} chars from resume, {len(jd_text)} chars from JD.")

    prompt = f"""
    You are an expert Corporate Career Advisor and Resume Reviewer. 
    Analyze the provided Resume against the Job Description.
    
    Job Description:
    {jd_text}
    
    Candidate Resume:
    {resume_text}
    
    Provide the output in exactly this structure:
    1. Resume Score: (out of 100 based on fit)
    2. Missing Skills: (Bullet points of what is lacking)
    3. Interview Roadmap: (Key concepts to study for this specific role)
    4. 3-Month Learning Plan: (A brief week-by-week guide to master the missing skills)
    """

    print("3. Calling Gemini API...")
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
    except Exception as e:
        print(f"gemini-3.6-flash error ({e}), retrying with fallback model...")
        time.sleep(2)
        response = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents=prompt
        )

    print("4. Successfully generated response!")
    return {"analysis": response.text}
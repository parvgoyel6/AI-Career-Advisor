import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import PyPDF2
import io

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reads key safely from the environment
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_text_from_pdf(pdf_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...)
):
    resume_text = extract_text_from_pdf(await resume.read())
    jd_text = extract_text_from_pdf(await job_description.read())
    
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
    
   try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
    except Exception as e:
        print(f"gemini-3.6-flash busy ({e}), trying gemini-3.1-pro-preview...")
        response = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents=prompt
        )
    
    return {"analysis": response.text}
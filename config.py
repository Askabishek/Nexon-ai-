import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# GROQ_MODEL = "llama3-70b-8192"
GROQ_MODEL = "llama-3.3-70b-versatile"

AGENT_CONFIDENCE_THRESHOLD = 0.4

AGENT_METADATA = {
    "career": {
        "name": "Career Agent",
        "icon": "💼",
        "description": "Jobs, resume, skills, interview prep",
        "keywords": [
            "job", "career", "resume", "interview", "salary", "work",
            "internship", "placement", "skills", "hire", "employment",
            "linkedin", "portfolio", "fresher", "switching"
        ],
    },
    "government": {
        "name": "Government Agent",
        "icon": "🏛️",
        "description": "Schemes, subsidies, welfare, documents",
        "keywords": [
            "scheme", "government", "subsidy", "welfare", "ration",
            "aadhaar", "pan", "passport", "pension", "pmkvy",
            "yojana", "benefit", "eligibility", "apply", "portal",
            "certificate", "loan", "mudra", "pm", "ministry"
        ],
    },
    "education": {
        "name": "Education Agent",
        "icon": "📚",
        "description": "Courses, exams, colleges, scholarships",
        "keywords": [
            "study", "exam", "college", "course", "scholarship",
            "jee", "neet", "gate", "university", "degree",
            "certification", "learn", "upskill", "tuition", "marks",
            "admission", "engineering", "medical", "arts"
        ],
    },
    "health": {
        "name": "Health Agent",
        "icon": "🩺",
        "description": "Wellness, symptoms, schemes, hospitals",
        "keywords": [
            "health", "doctor", "hospital", "medicine", "symptom",
            "ayushman", "insurance", "mental health", "diet",
            "exercise", "disease", "treatment", "clinic", "pharmacy",
            "wellness", "nutrition", "fitness", "stress"
        ],
    },
}

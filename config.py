import os
import json
import sys

# Determine the base directory dynamically based on whether the script is frozen (built as an executable)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)  # Directory of the executable
else:
    BASE_DIR = os.path.dirname(os.path.abspath(
        __file__))  # Directory of the script

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Load settings from settings.json


def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create default settings file if not exists
            default_settings = {
                "api_key": "",
                "default_models": [
                    "gemini-embedding-exp",
                    "gemini-1.5-pro",
                    "gemini-1.5-flash-8b",
                    "gemini-1.5-flash",
                    "gemini-2.0-flash-lite",
                    "gemini-2.0-flash",
                    "gemini-2.5-pro-preview-05-06",
                    "gemini-2.5-flash-preview-04-17"
                ],
                "custom_models": []
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(default_settings, f, indent=4)
            return default_settings
    except Exception as e:
        print(f"Error loading settings: {str(e)}")
        return {
            "api_key": "",
            "default_models": ["gemini-2.0-flash"],
            "custom_models": []
        }


# Load settings
SETTINGS = load_settings()

# API Configuration
GEMINI_API_KEY = SETTINGS.get("api_key", "")
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"  # Default model if none selected
DEFAULT_MODELS = SETTINGS.get("default_models", ["gemini-2.0-flash"])
CUSTOM_MODELS = SETTINGS.get("custom_models", [])
ALL_MODELS = DEFAULT_MODELS + CUSTOM_MODELS

# Save settings to file


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        global SETTINGS, GEMINI_API_KEY, ALL_MODELS, CUSTOM_MODELS
        SETTINGS = settings
        GEMINI_API_KEY = settings.get("api_key", "")
        CUSTOM_MODELS = settings.get("custom_models", [])
        ALL_MODELS = settings.get("default_models", []) + CUSTOM_MODELS
        return True
    except Exception as e:
        print(f"Error saving settings: {str(e)}")
        return False


PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
FILES_DIR = os.path.join(BASE_DIR, "files")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

# Default cache TTL in seconds (59 minutes)
DEFAULT_CACHE_TTL = 59 * 60

# Create directories if they don't exist
for directory in [PROFILES_DIR, FILES_DIR, CACHE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Default templates
DEFAULT_PERSONAL_CONTEXT = """
# Replace this with your personal information and experience
i am very passionate about software development and i have a strong background in computer science.
i have worked on several projects that have helped me develop my skills in programming, problem solving and teamwork.
i have done so and so projects that have helped me develop my skills in programming, problem solving and teamwork.

explain your self here. write about your passion, the reason you came in to this field, your past struggles and how you over came them, why you think you might be a good fit in this field etc
write as much as you can irrelevant of the field you are applying for and the ai will choose important points points on each generation based on the job description and use them to create a personalised and captivating cover letter. 
"""

DEFAULT_SYSTEM_INSTRUCTION_TEMPLATE = """
You are an expert in creating cover letters so attractive and professonal that the hiring manager will have no option but to hire the applicant.
You find common skills in the job description and in user to generate the perfect cover letter 
When creating you dont use skills that exist in job description but not in user because you know that leads to a very bad cover letter.
You learn as much as you can about the user when the user gives you information in the first prompt that says "sending info" for which you reply with "ok to proceed" after absorbing all possible information about the user.
in the following prompts, the user will then provide job descriptions for which you use the knowledge you have learned about the user to generate the perfect coverletter that is tailored to the job description by mentioning common skills found in both user and the job descripon only
"""

DEFAULT_SYSTEM_CORE_RULES = """when generating:
1. keep it professional 
2. Highlight relevant skills and experience common in description and user that match job requirements
3. IMPORTANT! do not include [enter stuff here] things on the coverletter like [enter your favourite experience here] or [Platform where you saw the advertisement] or [your name here]. the letter should be ready to send to the recruters. all the information you need is already provided.
4. do not include my lack of experience. but do not say i have experience either!. i.e do not lie, just omit
5. Make the letter approximately 250-400 words
6. do not include experience or technologies i have not have!i.r dont lie in the cover letter
7. if the skills mentioned in both the job description and the user is less, then say how my other skill can be transfered to similar skills in the job description. use users project to give examples of how the user has used similar skills in the past.
8. make sure to show the enthusiasm and curiousity the user mentions in his field, and tailor it to match whatever field the job description is about.
9. do not mention the lack of experience in a skill in the job description if the user also dont have it, intead, just mention the similar skill or he has learned similar skills in the past and how he utilised it in a practical project.
10. keep it positive. dont mention the dont haves and the lack of experience. instead, focus on the skills and the projects the user has done in the past that are similar to the job description. and show the hirer what a valuable asset the user will be to the company.
11. make sure there is only 1 new line after Sincerely, and the applicant name i.e name should apperar directly below Sincerely without any newline or empty space in between
"""

from google import genai
import constants as constants
import json
from google.genai.types import GenerateContentResponse
import re

def get_gemini_response(prompt):
    """
    Get response from Gemini LLM using the provided prompt.

    Args:
        prompt (str): The prompt to send to the Gemini LLM.

    Returns:
        str: The response from the Gemini LLM.
    """

    client = genai.Client(api_key=constants.GEMINI_API_KEY)

    response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
    # genai.configure(api_key=constants.GEMINI_API_KEY)
    # #gemini_llm = genai.GenerativeModel('gemini-1.5-flash')
    # gemini_llm = genai.GenerativeModel('gemini-2.0-flash',generation_config={"response_mime_type": "application/json"})
    # # gemini_llm = genai.GenerativeModel('gemini-2.0-flash',generation_config={"response_mime_type": "application/json"})
    # response = gemini_llm.generate_content(prompt)
    # #print(response)
    return response

def generate_prompt(resume_text, job_descrption, recommended_store):
    """
    Generate a prompt for the Gemini LLM based on the resume text, job description, and recommended store.

    Args:
        resume_text (str): The text extracted from the resume.
        job_descrption (str): The job description.
        recommended_store (str): The recommended store.

    Returns:
        str: The generated prompt.
    """
    prompt = f"""
    You are an expert resume analyzer. 
    Analyze the following resume text and job description to provide insights and suggestions for improvement. 
    Also, suggest relevant skills and keywords that should be included in the resume to better match the job description. 
    Finally, recommend a suitable store for further resources.

    Resume Text:
    {resume_text}

    Job Description:
    {job_descrption}

    Recommended Store:
    {recommended_store}

    Please provide your analysis in a structured format with clear sections for insights, suggestions, skills/keywords, and store recommendations.
    """
    return prompt

def format_llm_output(response):
    """
    Format the output from the Gemini LLM response.

    Args:
        response (GenerateContentResponse): The response from the Gemini LLM.

    Returns:
        dict: The formatted output.
    """
    try:
        # Extract the text content from the response
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'content'):
            response_text = response.content
        else:
            raise ValueError("Response does not contain text or content attribute")

        # Clean the response text to extract JSON from markdown code blocks
        # Remove markdown code block formatting if present
        if response_text.strip().startswith('```json'):
            # Extract content between ```json and ```
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
        elif response_text.strip().startswith('```'):
            # Extract content between ``` and ```
            json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

        # Attempt to parse the response text as JSON
        try:
            formatted_output = json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text in a dictionary
            formatted_output = {"raw_response": response_text}
        return formatted_output
    except Exception as e:
        print(f"Error formatting LLM output: {e}")
        return {"error": str(e)}

def generate_prompt_new(text_content,jd,recommended_score):
    
    """
    Generate a prompt for analyzing resumes against job descriptions.
 
    Args:
        text_content (str): The resume content.
        jd (list): List of job descriptions.
 
    Returns:
        str: The generated prompt.
    """

    resume_analysis_prompt = f"""
      Analyze the provided resume {text_content} and evaluate it against job descriptions {jd}. Extract structured information from {text_content} and compare it with each job description in {jd} to assess the candidate's fit for multiple roles. The evaluation should include detailed resume parsing and role-specific assessments.

      1. **Resume Parsing and Section Extraction**
        - Parse {text_content} to extract and structure the following sections:
          - **Personal Information**: Name, Email, Phone, LinkedIn, etc.
          - **Summary/Objective**: A brief professional summary or objective.
          - **Work Experience**: Company, Job Title, Start Date, End Date, Responsibilities, Achievements.
          - **Projects**: Project Name, Description.
          - **Skills**: Technical and soft skills listed as a list of dictionaries with skill and score (score to be calculated).
          - **Education**: College, Degree, Start Year, End Year, Percentage/CGPA.
          - **Certifications**: List of certifications.
          - **Other Relevant Sections**: Publications, Volunteering, Awards, etc. (if present).

      2. **Scoring Metrics for Resume**
        - **Overall Resume Score (0-100):**
          - Evaluated based on skills relevance, grammar quality, vocabulary, and formatting clarity.
        - **Grammar Score (1-10):**
          - Based on proper sentence structure, spelling, and punctuation.
        - **Formatting Score (1-10):**
          - Evaluates font consistency, spacing, readability, and section alignment.
        - **Vocabulary Score (1-10):**
          - Assesses the quality and variety of vocabulary used.
        - **Skill Score per Skill (0-10):**
          - Calculated based on years of experience, number of projects, and proficiency level indicated in {text_content}.
        - **Suggestions for Improvement:**
          - Provide recommendations for vocabulary, grammar, and formatting (scores to be included in suggestions section).

      3. **Evaluation Criteria for Each Job Description**
        - For each job description, **STRICTLY** extract exact title or role from {jd} and keep it same and short for every resume, then evaluate the resume based on:
          - **Score (0-100):**
            - Calculated based on the **relevance and actual usage** of the required skills from the job description in {text_content}.
            - **STRICTLY evaluate** whether each required skill in the JD is **explicitly used** in the candidate’s **work experience or projects**, not just listed in skills.
            - Also check for **years of experience** and context of usage (e.g., job roles, projects, certifications).
            - If skills are mentioned only in the skill list but not reflected in practical experience, consider them as **insufficient evidence**.
            - Assign score accordingly.
          - **Status** (Recommended or Not Recommended):
            - If score >= {recommended_score}, status must be **"recommended"**, even if resume is not fully aligned.
            - If score < {recommended_score}, status is **"not recommended"**.
            - Add explanation in **summary** if the resume is **not aligned** with the JD despite scoring above threshold.
          - **Resume styling score (0-10):**
            - Based on vocabulary, grammar, and formatting.
          - **Matched Skills:**
            - List top 3 matching skills from {text_content} that are required in the JD.
          - **Missing Skills:**
            - Identify up to 5 key skills required by the JD that are missing or insufficiently demonstrated in {text_content}.
          - **Suggestions:**
            - Provide recommendations for improving the resume to better align with the JD.
          - **Summary:**
            - Clear explanation of candidate’s fit. If status is "recommended" but alignment is weak, explicitly state "Resume is not aligned with the JD".

      4. **Overall Summary**
        - Provide a mandatory summary of the candidate's overall fit for all roles in {jd}. Clearly state which role(s) the candidate is best suited for and why.

      5. **STRICTLY JSON Output Format:**

      ```json
      {{
        "candidateName": "Charlie",
        "personal_information": {{
          "name": "Charlie",
          "email": "charlie@example.com",
          "phone": "+123456789",
          "linkedin": "linkedin.com/in/charlie"
        }},
        "summary": "Experienced software engineer with expertise in Python and AI.",
        "work_experience": [
          {{
            "company": "TechCorp",
            "job_title": "Software Engineer",
            "start_date": "2020-01",
            "end_date": "2023-06",
            "responsibilities": ["Developed AI models", "Led backend development"],
            "achievements": ["Reduced processing time by 30%"]
          }}
        ],
        "projects": [
          {{
            "name": "AI Chatbot",
            "description": ["Developed a chatbot using Python and NLP"]
          }}
        ],
        "skills": [
          {{
            "skill": "Python",
            "score": 8
          }},
          {{
            "skill": "Flask",
            "score": 7
          }}
        ],
        "education": [
          {{
            "college": "ABC University",
            "degree": "B.S. Computer Science",
            "start_year": "2015",
            "end_year": "2019",
            "percentage": "85%"
          }},
          {{
            "college": "XYZ High School",
            "start_year": "2013",
            "end_year": "2015",
            "cgpa": "9.2"
          }}
        ],
        "certifications": ["AWS Certified Solutions Architect"],
        "overall_score": 85,
        "overall_summary": "Candidate is a strong fit for Backend Developer role but does not align with DevOps or UI roles.",
        "evaluations": [{{
          "Backend Developer": {{
            "score": 68,
            "status":"recommended",
            "matchedSkills": "Python, Flask",
            "missing": "FastAPI, PostgreSQL",
            "suggest": "Consider including experience with FastAPI and relational databases",
            "summary": "Score meets threshold but resume is not fully aligned due to missing backend tech stack."
          }},
          "UI Developer": {{
            "score": 5,
            "status":"recommended",
            "matchedSkills": "Jira, XML, Communication",
            "missing": "Angular, React, JavaScript",
            "suggest": "Add experience with mandatory UI tech like React and Angular",
            "summary": "Score meets threshold but resume is not aligned with UI development requirements."
          }}
        }}],
        "resume_styling_score": 8
      }}
      ```
      5. **Processing Guidelines:**  
        - STRICTLY verify actual usage of required skills in JD by checking whether they appear in the candidate’s work experience or projects in {text_content}. Do not consider a skill sufficient if it is mentioned only in the skill list — there must be contextual evidence of usage (e.g., used in a project, job responsibility, or achievement).
        - Treat {text_content} as a single resume (not a list) and extract relevant details once for structuring sections and comparison against all job descriptions in {jd}.  
        - **STRICTLY** base evaluations on {text_content} and {jd} and extract title or role from {jd} and keep it same and short for every resume.  
        - Calculate skill scores based on evidence in {text_content} (e.g., years of experience, project involvement).  
        - For each job description, calculate the evaluation score by comparing the candidate’s skills and experience to the role’s requirements.  
        - Ensure matchedSkills and missing are concise, relevant, and derived from comparing {text_content} to the job description.  
        - Suggestions (both in evaluations and resume suggestions) should be actionable and specific.  
        - The summary in evaluations should provide a clear, high-level assessment of fit for each role.  
        - Maintain the exact JSON structure as shown above, with all keys unchanged.  
        - If certain fields (e.g., LinkedIn, achievements) are not found in {text_content}, leave them as empty strings or arrays as appropriate.  
        - Use "Unknown" for candidateName if the name cannot be extracted from {text_content}.
        - provide oversall summary of the candidate's resume with brief description explaining which {jd} is more suitable
      """    
    return resume_analysis_prompt
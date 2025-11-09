import base64
import io
import mimetypes
import uuid
from typing import List
from constants import MONGO_DB, MONGO_URI
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Form
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from PyPDF2 import PdfReader
import json
from fastapi.responses import StreamingResponse
import asyncio
from utils import (
    get_gemini_response,
    format_llm_output,
    generate_prompt,
    generate_prompt_new
)

# Initialize FastAPI app
router = APIRouter()

# Create async Mongo client
client = AsyncIOMotorClient(MONGO_URI)

# Access the database
db = client[MONGO_DB]

# Collection for resumes
files_collection = db["resume_analysis"]
files_data = db["resumes"]

@router.post("/upload_resume")  
async def upload_resume(
    request: Request,
    resume_file: UploadFile = File(...),
    job_description: UploadFile = File(...),
    recommended_store: int = 70
):

    """
    Upload a resume file, extract text, analyze it using Gemini LLM, and store the results in MongoDB.

    Args:
        request (Request): The FastAPI request object.
        file (UploadFile): The uploaded resume file.
        job_description (str): The job description to compare against.
        recommended_store (str): The recommended store for resources.
    Returns:
        JSONResponse: A response containing the analysis results or an error message.
    """

    try:
        # Validate file type
        if resume_file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        # Read and extract text from the PDF file
        pdf_reader = PdfReader(resume_file.file)
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text() + "\n"

        # Read job description file
        if job_description.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Job description must be a plain text file.")

        jd_pdf_reader = PdfReader(job_description.file)
        job_description_text = ""
        for page in jd_pdf_reader.pages:
            job_description_text += page.extract_text() + "\n"

        # Generate prompt for Gemini LLM
        #prompt = generate_prompt(resume_text, job_description_text, recommended_store)

        prompt = generate_prompt_new(resume_text, job_description_text, recommended_store)

        # Get response from Gemini LLM
        gemini_response = get_gemini_response(prompt)

        # Format the LLM output
        formatted_output = format_llm_output(gemini_response)

        # Prepare data to store in MongoDB
        file_id = str(uuid.uuid4())
        file_data = {
            "file_id": file_id,
            "filename": resume_file.filename,
            "content_type": resume_file.content_type,
            "resume_text": resume_text,
            "job_description": job_description_text,
            "recommended_store": recommended_store,
            "analysis": formatted_output
        }

        # Insert data into MongoDB
        await files_collection.insert_one(file_data)

        return JSONResponse(status_code=200, content={"message": "Resume analyzed and stored successfully.", "file_id": file_id, "analysis": formatted_output})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_analysis/{file_id}")
async def get_analysis(file_id: str):
    """
    Retrieve the analysis results for a given resume file ID from MongoDB.

    Args:
        file_id (str): The unique identifier of the resume file.
    Returns:
        JSONResponse: A response containing the analysis results or an error message.
    """
    try:
        # Fetch the document from MongoDB
        file_data = await files_collection.find_one({"file_id": file_id})

        if not file_data:
            raise HTTPException(status_code=404, detail="File not found.")

        # Remove MongoDB's internal ID before returning
        file_data["_id"] = str(file_data["_id"])

        return JSONResponse(status_code=200, content=file_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
app = FastAPI()

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Models
# --------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class CreateTask(BaseModel):
    title: str
    description:str
    target_date:str
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Resume Analyzer API"}

@app.post("/login")
async def login(request: LoginRequest):
    return {"message": "Login successful", "user": request.username}

@app.post("/create_task")
async def create_task(task: CreateTask):
    return {
        "message": "Task created successfully",
        "task": task
    }

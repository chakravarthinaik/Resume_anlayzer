from pydantic import BaseModel, EmailStr, validators
import datetime
import uuid
import json
import re
import time
from io import BytesIO
from tempfile import NamedTemporaryFile
from passlib.context import CryptContext
from jose import jwt
import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
    APIRouter,   
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
from constants import  MONGO_URI, MONGO_DB
from bson import ObjectId
import base64

router = APIRouter()
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
user_collection = db["Users"]

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
blacklisted_tokens = set()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    """
    Pydantic model for user registration.
    """
    username:str
    password:str
    confirm_password:str
    email:EmailStr
 
class userLogin(BaseModel):
    """
    Pydantic model for user login.
    """
    username:str
    password:str

def create_jwt_token(data: dict):
    """
    Generate a JWT token with expiration time.
 
    Args:
        data (dict): Data to encode in the token
 
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def create_user(user: User):
    """
    Register a user into MongoDB.
 
    Args:
        user (User): User registration data.
 
    Returns:
        dict: Success message.
    """
    user_dict = user.dict()
    await user_collection.insert_one(user_dict)
    return {"message": "User Saved successfully!"}

async def get_user_by_username(username: str):
    """
    Get user document from MongoDB by username.
 
    Args:
        username (str): The user's username.
 
    Returns:
        dict or None: User document.
    """
    user = await db.Users.find_one({"username": username})
    print(user)
    if user:
        user["_id"] = str(user["_id"])  # To avoid JSON serialization error
        return user
    return None

@router.post("/register")
async def register_user(user: User):
    """
    Endpoint to register a new user.
 
    Args:
        user (User): User registration data.
 
    Returns:
        dict: Success or error message.
    """
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
 
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
 
    user.password = pwd_context.hash(user.password)[:32]
    await create_user(user)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login_user(user: userLogin):
    """
    Endpoint to authenticate a user and return a JWT token.
 
    Args:
        user (userLogin): User login data.
    Returns:
        dict: JWT token or error message.
    """
    db_user = await get_user_by_username(user.username)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
 
    token_data = {"sub": db_user["username"]}
    token = create_jwt_token(token_data)
    return {"access_token": token, "token_type": "bearer"}
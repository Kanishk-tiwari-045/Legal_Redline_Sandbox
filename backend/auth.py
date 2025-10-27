import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configure password context with better bcrypt settings
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate password length
        if len(self.password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long")

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class User(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool = True

# In-memory user storage for prototype (use database in production)
users_db: dict = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate password if needed for bcrypt
    safe_password = _safe_password(plain_password)
    return pwd_context.verify(safe_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Truncate password if needed for bcrypt
    safe_password = _safe_password(password)
    return pwd_context.hash(safe_password)

def _safe_password(password: str) -> str:
    """
    Safely handle passwords longer than bcrypt's 72-byte limit.
    Uses SHA-256 to hash long passwords before bcrypt.
    """
    # bcrypt has a 72-byte limit
    if len(password.encode('utf-8')) <= 72:
        return password
    else:
        # Hash with SHA-256 first, then use bcrypt
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_user(user_data: UserCreate) -> User:
    if user_data.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user_id = str(len(users_db) + 1)
    hashed_password = get_password_hash(user_data.password)
    
    users_db[user_data.username] = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "is_active": True
    }
    
    return User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        is_active=True
    )

def authenticate_user(username: str, password: str) -> Optional[User]:
    user_data = users_db.get(username)
    if not user_data:
        return None
    
    if not verify_password(password, user_data["hashed_password"]):
        return None
    
    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        is_active=user_data["is_active"]
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

def get_user_by_username(username: str) -> Optional[User]:
    user_data = users_db.get(username)
    if not user_data:
        return None
    
    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        is_active=user_data["is_active"]
    )
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Any, Dict

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

# User Schemas
# This is what the user sends when creating an account
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# This is what your API will return when sending user info
# Notice there is NO password.
class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    last_active: datetime

    class Config:
        orm_mode = True # Tells Pydantic to read data from SQLAlchemy models
        
# This is what the frontend sends to add a message
class ChatData(BaseModel):
    session_id: int
    type: str         # "general" or "document"
    prompt: str       # The new user message
    history: List[Dict[str, Any]] # The array of past messages
    document_text: str | None = None

# This is what the API returns for a single message
class ChatMessage(BaseModel):
    id: int
    session_id: int
    message_content: str
    is_from_user: bool
    timestamp: datetime

    class Config:
        orm_mode = True

# This is what the API returns for a chat session
class ChatSession(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    messages: List[ChatMessage] = [] # You can optionally include messages

    class Config:
        orm_mode = True

# ClauseRewrite Schemas

# This is what the frontend sends to SAVE a rewrite
class ClauseRewriteCreate(BaseModel):
    original_text: str
    rewritten_text: str
    rationale: str

# This is what the API returns for a saved rewrite
class ClauseRewrite(BaseModel):
    id: int
    user_id: int
    original_text: str
    rewritten_text: str
    rationale: str
    created_at: datetime

    class Config:
        orm_mode = True
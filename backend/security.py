import os
from datetime import datetime, timedelta
from typing import Any, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

# Password Hashing
# Use bcrypt for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# JWT Token
# These values should come from your .env file
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_default_key_fallback")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Or whatever you prefer

if SECRET_KEY == "a_very_secret_default_key_fallback":
    print("WARNING: SECRET_KEY not set in .env. Using a weak default.")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
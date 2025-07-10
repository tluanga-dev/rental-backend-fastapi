from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Token models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: list[str] = []


class RefreshTokenData(BaseModel):
    user_id: int
    username: str


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False
    # Add more validation rules as needed
    return True


# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> Union[TokenData, RefreshTokenData]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Check token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise JWTError("Invalid token type")
        
        # Extract data based on token type
        if expected_type == "access":
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            scopes: list = payload.get("scopes", [])
            
            if username is None or user_id is None:
                raise JWTError("Invalid token payload")
            
            return TokenData(username=username, user_id=user_id, scopes=scopes)
        
        elif expected_type == "refresh":
            user_id: int = payload.get("user_id")
            username: str = payload.get("sub")
            
            if user_id is None or username is None:
                raise JWTError("Invalid refresh token payload")
            
            return RefreshTokenData(user_id=user_id, username=username)
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_token_pair(user_id: int, username: str, scopes: list = None) -> Token:
    """Create both access and refresh tokens"""
    if scopes is None:
        scopes = []
    
    # Create access token
    access_token_data = {
        "sub": username,
        "user_id": user_id,
        "scopes": scopes
    }
    access_token = create_access_token(access_token_data)
    
    # Create refresh token
    refresh_token_data = {
        "sub": username,
        "user_id": user_id
    }
    refresh_token = create_refresh_token(refresh_token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
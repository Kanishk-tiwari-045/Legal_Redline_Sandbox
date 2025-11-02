from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(120), unique=True, index=True)
    password_hash = Column(String(255))
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # A User can have many ChatSessions and many ClauseRewrites
    chat_sessions = relationship("ChatSession", back_populates="user")
    rewrites = relationship("ClauseRewrite", back_populates="user")

# Chat Models
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # A ChatSession belongs to one User and has many ChatMessages
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    message_content = Column(Text)
    is_from_user = Column(Boolean, default=True) # True for user, False for AI
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # A ChatMessage belongs to one ChatSession
    session = relationship("ChatSession", back_populates="messages")

# Rewrite Model
class ClauseRewrite(Base):
    __tablename__ = "clause_rewrites"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_text = Column(Text)
    rewritten_text = Column(Text)
    rationale = Column(Text) # <-- The important field you added
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # A ClauseRewrite belongs to one User
    user = relationship("User", back_populates="rewrites")
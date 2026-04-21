from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    full_name = Column(String)
    username = Column(String, nullable=True)
    diamonds = Column(BigInteger, default=500) # Give some starting diamonds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stats = relationship("GameStat", back_populates="user")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class GameStat(Base):
    __tablename__ = "game_stats"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    game_type = Column(String) # e.g., "codenames"
    result = Column(String) # e.g., "win", "loss"
    played_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="stats")

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(JSON, default=dict)

"""
Database models for module and camera registration.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base


class Camera(Base):
    """Camera configuration stored in database"""
    __tablename__ = "cameras"
    
    camera_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    stream_quality = Column(String(20), default="stream2", nullable=False)
    description = Column(Text, default="")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Camera(camera_id={self.camera_id}, name={self.name}, ip={self.ip_address})>"



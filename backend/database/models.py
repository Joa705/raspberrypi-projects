"""
Database models for module and camera registration.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.db import Base
import uuid


class Module(Base):
    """Model for storing registered modules (camera, sensor, heat, etc.)."""
    __tablename__ = "modules"
    
    module_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    module_type = Column(String(50), nullable=False)  # camera, sensor, heat, etc.
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)  # Module service URL
    status = Column(String(20), default="offline")  # online, offline, error
    last_seen = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to cameras
    cameras = relationship("Camera", back_populates="module")
    
    def __repr__(self):
        return f"<Module(module_id={self.module_id}, type={self.module_type})>"


class Camera(Base):
    """Model for storing individual cameras managed by a camera module."""
    __tablename__ = "cameras"
    
    camera_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.module_id"), nullable=False)
    stream_url = Column(String(500), nullable=True)  # Individual camera stream URL
    location = Column(String(200), nullable=True)
    resolution = Column(String(50), nullable=True)  # e.g., "1920x1080"
    status = Column(String(20), default="offline")  # online, offline, error
    last_seen = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to module
    module = relationship("Module", back_populates="cameras")
    
    def __repr__(self):
        return f"<Camera(camera_id={self.camera_id}, name={self.name})>"

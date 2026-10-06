from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="student") # student, organizer, faculty
    
    events = relationship("Event", back_populates="organizer")
    registrations = relationship("Registration", back_populates="user")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String)
    date_time = Column(DateTime)
    venue = Column(String)
    capacity = Column(Integer)
    status = Column(String, default="pending") # pending, active, completed, cancelled
    waitlist_enabled = Column(Boolean, default=True)
    
    organizer_id = Column(Integer, ForeignKey("users.id"))
    organizer = relationship("User", back_populates="events")
    registrations = relationship("Registration", back_populates="event")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="registered") # registered, waitlisted, cancelled
    present = Column(Boolean, default=False)
    
    # Registration details
    phone = Column(String, nullable=True)
    dietary = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    
    event = relationship("Event", back_populates="registrations")
    user = relationship("User", back_populates="registrations")
    
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

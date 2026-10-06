import os
import random
from datetime import datetime, timedelta, timezone
from .database import SessionLocal, engine
from . import models
from .auth import get_password_hash

def seed_data():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    hashed_pw = get_password_hash("password123")
    
    # 1. Hierarchy: Admin, Faculty, Organizers, Students
    admin = models.User(name="Super Admin", email="admin@example.com", hashed_password=hashed_pw, role="admin")
    faculty1 = models.User(name="Prof. Smith", email="smith@faculty.edu", hashed_password=hashed_pw, role="faculty")
    faculty2 = models.User(name="Dr. Jones", email="jones@faculty.edu", hashed_password=hashed_pw, role="faculty")
    
    organizer1 = models.User(name="Tech Club", email="tech@organizer.edu", hashed_password=hashed_pw, role="organizer")
    organizer2 = models.User(name="Arts Society", email="arts@organizer.edu", hashed_password=hashed_pw, role="organizer")
    organizer3 = models.User(name="Sports Council", email="sports@organizer.edu", hashed_password=hashed_pw, role="organizer")
    
    db.add_all([admin, faculty1, faculty2, organizer1, organizer2, organizer3])
    
    students = []
    for i in range(1, 16):
        student = models.User(name=f"Student {i}", email=f"student{i}@example.com", hashed_password=hashed_pw, role="student")
        db.add(student)
        students.append(student)
        
    db.commit()
    
    # 2. Events across organizers
    now = datetime.now(timezone.utc)
    events_data = [
        ("AI Symposium 2026", "A deep dive into Generative AI.", "Conference", now + timedelta(days=5), "Auditorium", 10, "active", organizer1.id),
        ("HackTheCampus", "24-hour coding marathon.", "Hackathon", now + timedelta(days=15), "Innovation Lab", 50, "active", organizer1.id),
        ("Web3 Workshop", "Learn Solidity and smart contracts.", "Workshop", now + timedelta(days=2), "Room 302", 30, "pending", organizer1.id),
        
        ("Spring Art Gala", "Showcase of student art projects.", "Exhibition", now + timedelta(days=7), "Main Gallery", 100, "active", organizer2.id),
        ("Pottery Masterclass", "Hands on pottery session.", "Workshop", now + timedelta(days=20), "Studio B", 5, "active", organizer2.id),
        
        ("Inter-College Basketball", "Annual basketball tournament.", "Sports", now + timedelta(days=3), "Sports Arena", 200, "active", organizer3.id),
        ("Yoga Retreat", "Morning yoga for mental health.", "Health", now + timedelta(days=1), "Campus Lawn", 50, "pending", organizer3.id),
    ]
    
    events = []
    for title, desc, cat, dt, venue, cap, status, org_id in events_data:
        e = models.Event(
            title=title, description=desc, category=cat, date_time=dt, venue=venue, 
            capacity=cap, status=status, organizer_id=org_id
        )
        db.add(e)
        events.append(e)
    
    db.commit()
    
    # 3. Registrations (Lots of demo data)
    # The AI Symposium capacity is 10. We will register all 15 students to trigger waitlist!
    ai_event = next(e for e in events if "AI Symposium" in e.title)
    pottery_event = next(e for e in events if "Pottery" in e.title)
    
    for i, s in enumerate(students):
        # 15 students register for AI Symposium (10 capacity)
        status = "registered" if i < ai_event.capacity else "waitlisted"
        reg1 = models.Registration(event_id=ai_event.id, user_id=s.id, status=status, present=(i % 3 == 0))
        db.add(reg1)
        
        # 10 students register for Pottery (5 capacity)
        if i < 10:
            status2 = "registered" if i < pottery_event.capacity else "waitlisted"
            reg2 = models.Registration(event_id=pottery_event.id, user_id=s.id, status=status2)
            db.add(reg2)
            
        # Random registrations for others
        for e in events:
            if e.id not in [ai_event.id, pottery_event.id] and random.random() > 0.6:
                reg3 = models.Registration(event_id=e.id, user_id=s.id, status="registered")
                db.add(reg3)
                
    db.commit()
    db.close()
    print("Full Hierarchy and Demo Data seeded successfully!")

if __name__ == "__main__":
    seed_data()

import os
import django
from datetime import timedelta
from django.utils import timezone
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_campus.settings')
django.setup()

from events.models import User, Event, Registration

def run():
    print("Creating users...")
    users = []
    roles = ['student', 'student', 'student', 'organizer', 'faculty', 'admin']
    
    for i, role in enumerate(roles):
        username = f"{role}{i}"
        user, created = User.objects.get_or_create(username=username, defaults={
            'email': f'{username}@campus.edu',
            'role': role,
            'department': 'Computer Science' if role == 'faculty' else ''
        })
        if created:
            user.set_password('password123')
            user.save()
        users.append(user)

    organizer = [u for u in users if u.role == 'organizer'][0]
    students = [u for u in users if u.role == 'student']
    
    print("Creating events...")
    events_data = [
        {
            'title': 'Tech Symposium 2026',
            'description': 'Annual technology symposium featuring guest speakers from top tech companies, hands-on workshops, and networking opportunities. Join us to explore the future of AI, cloud computing, and cybersecurity.',
            'category': 'Conference',
            'date': (timezone.now() + timedelta(days=5)).date(),
            'time': '10:00:00',
            'venue': 'Main Auditorium',
            'capacity': 200,
            'status': 'active',
            'waitlist_enabled': True
        },
        {
            'title': 'AI Hackathon',
            'description': 'A 24-hour hackathon focused on building innovative solutions using Generative AI. Mentors will be available to help teams. Food and drinks provided!',
            'category': 'Hackathon',
            'date': (timezone.now() + timedelta(days=12)).date(),
            'time': '18:00:00',
            'venue': 'Innovation Lab',
            'capacity': 50,
            'status': 'active',
            'waitlist_enabled': True
        },
        {
            'title': 'Career Fair Fall 2026',
            'description': 'Meet with recruiters from over 50 companies looking for interns and full-time hires. Bring copies of your resume and dress professionally.',
            'category': 'Career',
            'date': (timezone.now() + timedelta(days=2)).date(),
            'time': '09:00:00',
            'venue': 'Campus Recreation Center',
            'capacity': 500,
            'status': 'pending',
            'waitlist_enabled': False
        },
        {
            'title': 'Introduction to Cloud Computing',
            'description': 'A beginner-friendly workshop on AWS, Azure, and Google Cloud basics. Learn how to deploy your first web application to the cloud.',
            'category': 'Workshop',
            'date': (timezone.now() + timedelta(days=20)).date(),
            'time': '14:00:00',
            'venue': 'Room 402, Engineering Bldg',
            'capacity': 30,
            'status': 'active',
            'waitlist_enabled': True
        }
    ]

    events = []
    for data in events_data:
        event, _ = Event.objects.get_or_create(
            title=data['title'],
            defaults={
                'description': data['description'],
                'category': data['category'],
                'date': data['date'],
                'time': data['time'],
                'venue': data['venue'],
                'capacity': data['capacity'],
                'status': data['status'],
                'waitlist_enabled': data['waitlist_enabled'],
                'organizer': organizer
            }
        )
        events.append(event)
        
    print("Registering students...")
    active_events = [e for e in events if e.status == 'active']
    for student in students:
        for event in active_events:
            if random.choice([True, False]): # 50% chance to register
                Registration.objects.get_or_create(event=event, user=student, defaults={'status': 'registered'})
                
    print("Demo data successfully created!")

if __name__ == "__main__":
    run()

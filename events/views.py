from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, Registration, Attendance, EventApproval
from django.db.models import Count
from django.utils import timezone

def event_list(request):
    events = Event.objects.filter(status='active').order_by('date', 'time')
    return render(request, 'events/event_list.html', {'events': events})

@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    registered = False
    if request.user.is_authenticated:
        registered = Registration.objects.filter(event=event, user=request.user, status__in=['registered', 'waitlisted']).exists()
    
    context = {
        'event': event,
        'registered': registered,
        'spots_filled': event.registrations.filter(status='registered').count()
    }
    return render(request, 'events/event_detail.html', context)

@login_required
def register_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.status != 'active':
        messages.error(request, "This event is not active.")
        return redirect('event_detail', pk=pk)
        
    registration, created = Registration.objects.get_or_create(event=event, user=request.user)
    if not created and registration.status in ['registered', 'waitlisted']:
        messages.info(request, "You are already registered for this event.")
        return redirect('event_detail', pk=pk)
        
    current_registrations = event.registrations.filter(status='registered').count()
    if current_registrations >= event.capacity:
        if event.waitlist_enabled:
            registration.status = 'waitlisted'
            registration.save()
            messages.success(request, "Event is full. You have been added to the waitlist.")
        else:
            messages.error(request, "Event is full and waitlist is not enabled.")
            registration.delete()
    else:
        registration.status = 'registered'
        registration.save()
        messages.success(request, "Successfully registered for the event!")
        
    return redirect('event_detail', pk=pk)

@login_required
def dashboard(request):
    user = request.user
    context = {'user_role': user.role}
    
    if user.role == 'student':
        registrations = Registration.objects.filter(user=user).order_by('-registered_at')
        context['registrations'] = registrations
    elif user.role in ['organizer', 'admin']:
        events = Event.objects.filter(organizer=user) if user.role == 'organizer' else Event.objects.all()
        context['events'] = events
    elif user.role == 'faculty':
        pending_events = Event.objects.filter(status='pending')
        context['pending_events'] = pending_events
        
    return render(request, 'events/dashboard.html', context)

@login_required
def approve_event(request, pk):
    if request.user.role not in ['admin', 'faculty']:
        messages.error(request, "Unauthorized.")
        return redirect('dashboard')
        
    event = get_object_or_404(Event, pk=pk)
    event.status = 'active'
    event.save()
    EventApproval.objects.create(event=event, approver=request.user, decision='approved')
    messages.success(request, f"Event '{event.title}' has been approved.")
    return redirect('dashboard')

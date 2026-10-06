from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Event, Registration, Notification, Attendance, EventApproval

admin.site.register(User, UserAdmin)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'time', 'organizer', 'capacity', 'status')
    list_filter = ('status', 'category', 'date')
    search_fields = ('title', 'description')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'registered_at')
    list_filter = ('status', 'event')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'type', 'sent_at', 'is_read')
    list_filter = ('is_read', 'type')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('registration', 'present', 'marked_at')
    list_filter = ('present',)

@admin.register(EventApproval)
class EventApprovalAdmin(admin.ModelAdmin):
    list_display = ('event', 'approver', 'decision', 'created_at')
    list_filter = ('decision',)

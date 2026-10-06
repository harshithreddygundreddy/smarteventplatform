from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/<int:pk>/register/', views.register_event, name='register_event'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('event/<int:pk>/approve/', views.approve_event, name='approve_event'),
]

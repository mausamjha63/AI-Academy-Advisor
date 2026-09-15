from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.advisor_chat, name='advisor_chat'),
    path('chat/history/', views.get_chat_history, name='get_chat_history'),
    path('chat/messages/<int:session_id>/', views.get_chat_messages, name='get_chat_messages'),
]

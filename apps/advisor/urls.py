from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.advisor_chat, name='advisor_chat'),
    path('chat/history/', views.get_chat_history, name='get_chat_history'),
    path('chat/messages/<int:session_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('chat/delete/<int:session_id>/', views.delete_chat_session, name='delete_chat_session'),
    path('chat/delete_all/', views.delete_all_chats, name='delete_all_chats'),
    path('upload_document/', views.upload_document, name='upload_document'),
]

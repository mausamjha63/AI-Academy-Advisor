from django.shortcuts import render
from django.http import JsonResponse
from .services.advisor_service import AdvisorService
from students.models import Student
from .models import ChatSession, ChatMessage
import json

def advisor_chat(request):
    if request.method == "POST":
        query = request.POST.get('query')
        student_id = request.POST.get('student_id')
        session_id = request.POST.get('session_id')
        
        # 1. Fetch or create session
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                session = None
        else:
            session = None
            
        if not session:
            # Generate short title from query
            title_words = query.split()[:5]
            title = " ".join(title_words) + ("..." if len(query.split()) > 5 else "")
            if not title.strip():
                title = "New Academic Chat"
            session = ChatSession.objects.create(
                title=title,
                student_id=student_id if student_id else None
            )
            
        # 2. Save User Message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content={'text': query}
        )
        
        # 3. Process Query
        service = AdvisorService()
        response = service.process_query(query, student_id)
        
        # 4. Save Assistant Message
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=response
        )
        
        # Attach session_id so frontend knows it
        response['session_id'] = session.id
        
        return JsonResponse(response)
        
    synthetic_students = Student.objects.all()
    return render(request, 'advisor/chat.html', {'synthetic_students': synthetic_students})

def get_chat_history(request):
    student_id = request.GET.get('student_id')
    
    sessions = ChatSession.objects.all()
    if student_id:
        sessions = sessions.filter(student_id=student_id)
    else:
        sessions = sessions.filter(student_id__isnull=True)
        
    sessions = sessions.order_by('-updated_at')
    
    data = []
    for s in sessions:
        data.append({
            'id': s.id,
            'title': s.title,
            'updated_at': s.updated_at.isoformat()
        })
    return JsonResponse({'sessions': data})

def get_chat_messages(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
        messages = session.messages.order_by('timestamp')
        data = []
        for m in messages:
            data.append({
                'role': m.role,
                'content': m.content,
                'timestamp': m.timestamp.isoformat()
            })
        return JsonResponse({'messages': data})
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)

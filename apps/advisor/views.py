from django.shortcuts import render
from django.http import JsonResponse
from .services.advisor_service import AdvisorService
from students.models import Student
from .models import ChatSession, ChatMessage
import json
from pypdf import PdfReader
import pandas as pd
from google import genai

def advisor_chat(request):
    if request.method == "POST":
        query = request.POST.get('query')
        student_id = request.POST.get('student_id')
        session_id = request.POST.get('session_id')
        
        # 1. Fetch or create session
        if session_id and session_id not in ['undefined', 'null', '']:
            try:
                session = ChatSession.objects.get(id=session_id)
            except (ChatSession.DoesNotExist, ValueError):
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
        response = service.process_query(query, student_id, session_id=session.id)
        
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

def upload_document(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request method'}, status=405)
        
    try:
        uploaded_file = request.FILES.get('file')
        session_id = request.POST.get('session_id')
        
        if not uploaded_file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
            
        # File size validation (e.g., 5MB limit)
        if uploaded_file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File size exceeds 5MB limit'}, status=400)
            
        # File type validation
        filename = uploaded_file.name
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if ext not in ['pdf', 'xlsx']:
            return JsonResponse({'error': f'Unsupported file type: {ext}'}, status=400)
            
        # Fetch or create session
        session = None
        if session_id and session_id not in ['undefined', 'null', '']:
            try:
                session = ChatSession.objects.get(id=session_id)
            except (ChatSession.DoesNotExist, ValueError):
                pass
            
        if not session:
            session = ChatSession.objects.create(title=f"Chat with {filename}")
            
        # Create Document record
        from .models import UploadedDocument, UploadedDocumentChunk
        doc = UploadedDocument.objects.create(session=session, filename=filename)
        
        client = genai.Client()
        
        # Extract and store chunks
        chunks_created = 0
        if ext == 'pdf':
            reader = PdfReader(uploaded_file)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    try:
                        res = client.models.embed_content(model='gemini-embedding-2', contents=text.strip())
                        embedding = res.embeddings[0].values
                    except Exception as embed_e:
                        print(f"Embedding failed: {embed_e}")
                        embedding = None
                        
                    UploadedDocumentChunk.objects.create(
                        document=doc,
                        content=text.strip(),
                        page_or_sheet=f"Page {i+1}",
                        embedding=embedding
                    )
                    chunks_created += 1
        elif ext == 'xlsx':
            df_dict = pd.read_excel(uploaded_file, sheet_name=None)
            for sheet_name, df in df_dict.items():
                for index, row in df.iterrows():
                    row_dict = row.dropna().to_dict()
                    if row_dict:
                        content = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])
                        try:
                            res = client.models.embed_content(model='gemini-embedding-2', contents=content)
                            embedding = res.embeddings[0].values
                        except Exception as embed_e:
                            print(f"Embedding failed: {embed_e}")
                            embedding = None
                            
                        UploadedDocumentChunk.objects.create(
                            document=doc,
                            content=content,
                            page_or_sheet=f"{sheet_name} - Row {index+2}",
                            embedding=embedding
                        )
                        chunks_created += 1
                            
        if chunks_created == 0:
            return JsonResponse({'error': 'No readable content found in file'}, status=400)
                
        return JsonResponse({
            'success': True,
            'message': 'Document uploaded successfully',
            'filename': filename,
            'session_id': session.id
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to process file: {str(e)}'}, status=500)

from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.conf import settings

from students.models import Student, StudentCourseHistory
from academics.models import Course, CourseOffering, Prerequisite
from django.db.models import Sum
from rag.models import DocumentChunk

def get_chunk_count():
    try:
        return DocumentChunk.objects.filter(embedding__isnull=False).count()
    except Exception:
        return "Unknown"

def landing_page(request):
    return render(request, 'core/landing.html')

def signin_page(request):
    return render(request, 'core/signin.html')

def signup_page(request):
    return render(request, 'core/signup.html')

def dashboard(request):
    synthetic_students = Student.objects.all()
    active_student = None
    
    student_id = request.GET.get('student_id')
    if student_id:
        active_student = Student.objects.filter(student_id=student_id).first()
        
    stats = {
        'courses_count': Course.objects.count(),
        'students_count': Student.objects.count(),
        'offerings_count': CourseOffering.objects.count(),
        'prereq_count': Prerequisite.objects.count(),
        'chunks_count': get_chunk_count(), 
    }
    
    context = {
        'synthetic_students': synthetic_students,
        'active_student': active_student,
        'stats': stats,
    }
    return render(request, 'core/dashboard.html', context)

def system_status(request):
    db_status = "OK"
    try:
        connection.ensure_connection()
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
        
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    gemini_status = "Active" if gemini_key and gemini_key != 'mock_key_for_testing' else "Fallback Mode"
    
    synthetic_students = Student.objects.all()
    
    context = {
        'db_status': db_status,
        'app_status': 'OK',
        'gemini_status': gemini_status,
        'synthetic_students': synthetic_students,
    }
    return render(request, 'core/system_status.html', context)

def students_list(request):
    context = {
        'synthetic_students': Student.objects.all(),
        'active_student': Student.objects.filter(student_id=request.GET.get('student_id')).first() if request.GET.get('student_id') else None,
    }
    return render(request, 'core/students.html', context)

def academic_structure(request):
    context = {
        'synthetic_students': Student.objects.all(),
        'active_student': Student.objects.filter(student_id=request.GET.get('student_id')).first() if request.GET.get('student_id') else None,
        'offerings': CourseOffering.objects.select_related('course').all()[:100],
    }
    return render(request, 'core/academic_structure.html', context)

def documents_sources(request):
    context = {
        'synthetic_students': Student.objects.all(),
        'active_student': Student.objects.filter(student_id=request.GET.get('student_id')).first() if request.GET.get('student_id') else None,
    }
    return render(request, 'core/documents.html', context)

def administration(request):
    db_status = "OK"
    try:
        connection.ensure_connection()
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    gemini_status = "Active" if gemini_key and gemini_key != 'mock_key_for_testing' else "Fallback Mode"
    
    context = {
        'synthetic_students': Student.objects.all(),
        'active_student': Student.objects.filter(student_id=request.GET.get('student_id')).first() if request.GET.get('student_id') else None,
        'db_status': db_status,
        'gemini_status': gemini_status,
        'stats': {
            'courses': Course.objects.count(),
            'offerings': CourseOffering.objects.count(),
            'students': Student.objects.count(),
            'prereqs': Prerequisite.objects.count(),
            'chunks': get_chunk_count(),
        }
    }
    return render(request, 'core/administration.html', context)

def global_search(request):
    q = request.GET.get('q', '').strip()
    student_id = request.GET.get('student_id', '')
    
    if not q:
        return render(request, 'core/search_results.html', {
            'query': q,
            'courses': [],
            'empty': True,
            'synthetic_students': Student.objects.all(),
            'active_student': Student.objects.filter(student_id=student_id).first() if student_id else None,
        })
    
    # 1. Exact course code match
    q_upper = q.upper().replace(' ', '')
    exact_course = Course.objects.filter(course_code__iexact=q_upper).first()
    if exact_course:
        from django.shortcuts import redirect
        from django.urls import reverse
        url = reverse('course_detail', kwargs={'course_code': exact_course.course_code})
        if student_id:
            url += f"?student_id={student_id}"
        return redirect(url)
    
    # 2. Rule query / Natural language routing
    # If it contains question words or academic rule keywords
    nl_keywords = ['what', 'how', 'when', 'why', 'attendance', 'cgpa', 'progression', 'registration', 'summer term', 'minimum']
    q_lower = q.lower()
    
    # Handle pure greetings
    if q_lower in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']:
        return render(request, 'core/search_results.html', {
            'query': q,
            'courses': [],
            'greeting': True,
            'synthetic_students': Student.objects.all(),
            'active_student': Student.objects.filter(student_id=student_id).first() if student_id else None,
        })
        
    # Handle non-academic queries (basic heuristic)
    if 'weather' in q_lower or 'sports' in q_lower:
        return render(request, 'core/search_results.html', {
            'query': q,
            'courses': [],
            'out_of_scope': True,
            'synthetic_students': Student.objects.all(),
            'active_student': Student.objects.filter(student_id=student_id).first() if student_id else None,
        })

    is_nl = any(kw in q_lower for kw in nl_keywords) or '?' in q
    if is_nl:
        from django.shortcuts import redirect
        from django.urls import reverse
        url = reverse('advisor_chat')
        params = []
        if student_id:
            params.append(f"student_id={student_id}")
        params.append(f"q={q}")
        if params:
            url += "?" + "&".join(params)
        return redirect(url)
        
    # 3. Course Title Match
    courses = Course.objects.filter(title__icontains=q)
    if courses.count() == 1:
        from django.shortcuts import redirect
        from django.urls import reverse
        url = reverse('course_detail', kwargs={'course_code': courses.first().course_code})
        if student_id:
            url += f"?student_id={student_id}"
        return redirect(url)
        
    return render(request, 'core/search_results.html', {
        'query': q,
        'courses': courses,
        'synthetic_students': Student.objects.all(),
        'active_student': Student.objects.filter(student_id=student_id).first() if student_id else None,
    })

from academics.models import Course, CourseOffering, Prerequisite
from django.db.models import Q

class AcademicDataService:
    @staticmethod
    def get_course_info(course_code):
        try:
            return Course.objects.get(course_code__iexact=course_code)
        except Course.DoesNotExist:
            return None
            
    @staticmethod
    def get_prerequisites(course_code):
        course = AcademicDataService.get_course_info(course_code)
        if not course:
            return None
        return list(Prerequisite.objects.filter(course=course))
        
    @staticmethod
    def get_course_offerings(course_code, semester=None, batch=None):
        course = AcademicDataService.get_course_info(course_code)
        if not course:
            return None
            
        offerings = CourseOffering.objects.filter(course=course)
        if semester:
            offerings = offerings.filter(semester=semester)
        if batch:
            offerings = offerings.filter(batch_context__icontains=batch)
            
        return list(offerings)

    @staticmethod
    def search_courses(query_text, limit=15):
        import string
        stopwords = {'course', 'code', 'for', 'of', 'in', 'the', 'what', 'is', 'are', 'show', 'me', 'list', 'give', 'codes', 'which', 'offered', 'under', 'minor', 'major', 'courses'}
        clean_query = query_text.lower().translate(str.maketrans('', '', string.punctuation))
        tokens = [w for w in clean_query.split() if w not in stopwords and len(w) > 2]
        
        if not tokens:
            return []
            
        q_objects = Q()
        for token in tokens:
            q_objects |= Q(title__icontains=token) | Q(programme_applicability__icontains=token) | Q(course_code__icontains=token)
            
        return list(Course.objects.filter(q_objects).distinct()[:limit])

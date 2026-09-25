import os
import string
import json
import re
from google import genai
from django.conf import settings
from .retrieval_service import RetrievalService
from .academic_data_service import AcademicDataService
from .decision_engine import DecisionEngine
from advisor.prompts import get_prompt_builder

class AdvisorService:
    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def _classify_intent(self, query: str) -> str:
        clean_query = query.strip().lower()
        # 1. Greeting
        if clean_query in ["hi", "hello", "hey", "good morning", "good afternoon", "greetings"]:
            return "GREETING"
            
        # 2. Out of Scope (lightweight deterministic rules)
        out_of_scope_keywords = ["how are you", "tell me a joke", "what is the weather", "weather", "write python", "python code", "elon musk", "who are you"]
        for kw in out_of_scope_keywords:
            if kw in clean_query:
                return "OUT_OF_SCOPE"
                
        # 3. Prompt injection interception
        injection_keywords = ["ignore", "forget", "reveal", "prompt", "you are an", "system instructions", "own knowledge", "unrestricted assistant"]
        for kw in injection_keywords:
            if kw in clean_query:
                return "OUT_OF_SCOPE"
                
        # 4. Needs clarification
        if clean_query in ["what is the prerequisite?", "can i take this course?", "is it offered?"]:
            return "NEEDS_CLARIFICATION"

        return "ACADEMIC_IN_SCOPE"

    def process_query(self, user_query, student_id=None, session_id=None):
        intent = self._classify_intent(user_query)
        
        if intent == "GREETING":
            return self._build_response(
                "ANSWERED", 
                "Hello! I’m the AI Academic Advisor. I can help you with university academic regulations, courses, prerequisites, semester offerings, registration, progression, attendance, and eligibility. What would you like to know?", 
                []
            )
            
        if intent == "OUT_OF_SCOPE":
            return self._build_response(
                DecisionEngine.STATES['OUT_OF_SCOPE'],
                "I’m the AI Academic Advisor. I can help with university academic questions such as academic regulations, course information, prerequisites, semester offerings, registration, progression, attendance, and eligibility. Please ask an academic question related to the university.",
                []
            )
            
        if intent == "NEEDS_CLARIFICATION":
            return self._build_response(
                DecisionEngine.STATES['NEEDS_MORE_INFORMATION'],
                "Please specify which course or programme you are referring to so I can provide accurate academic information.",
                []
            )
            
        # ACADEMIC_IN_SCOPE
        
        # 1. Retrieve RAG evidence
        rag_evidence = self.retrieval_service.retrieve_evidence(user_query, top_k=3)
        
        # 2. Extract potential course codes for structured data
        words = user_query.upper().split()
        potential_codes = [w.strip(string.punctuation) for w in words if any(char.isdigit() for char in w)]
        structured_evidence = []
        for code in potential_codes:
            course = AcademicDataService.get_course_info(code)
            if course:
                prereqs = AcademicDataService.get_prerequisites(code)
                offerings = AcademicDataService.get_course_offerings(code)
                
                prereq_str = "None"
                if prereqs:
                    prereq_str = "; ".join([p.prerequisite_condition for p in prereqs])
                    
                offering_str = "Unknown"
                if offerings:
                    offering_str = "; ".join([f"Sem {o.semester} ({o.academic_year})" for o in offerings])
                
                structured_evidence.append({
                    "content": f"Course: {course.course_code} - {course.title}, Credits: {course.credits}. Programme: {course.programme_applicability}. Prerequisites: {prereq_str}. Offerings: {offering_str}.",
                    "source": course.source_metadata.get('source_file', 'Structured Database') if course.source_metadata else 'Structured Database',
                    "page": course.source_metadata.get('sheet_name', '') if course.source_metadata else '',
                    "metadata": course.source_metadata
                })
                
        # If no explicit course codes were extracted, try a natural language search against structured data
        if not potential_codes and not structured_evidence:
            search_results = AcademicDataService.search_courses(user_query)
            for course in search_results:
                prereqs = AcademicDataService.get_prerequisites(course.course_code)
                offerings = AcademicDataService.get_course_offerings(course.course_code)
                
                prereq_str = "None"
                if prereqs:
                    prereq_str = "; ".join([p.prerequisite_condition for p in prereqs])
                    
                offering_str = "Unknown"
                if offerings:
                    offering_str = "; ".join([f"Sem {o.semester} ({o.academic_year})" for o in offerings])
                
                structured_evidence.append({
                    "content": f"Course: {course.course_code} - {course.title}, Credits: {course.credits}. Programme: {course.programme_applicability}. Prerequisites: {prereq_str}. Offerings: {offering_str}.",
                    "source": course.source_metadata.get('source_file', 'Structured Database') if course.source_metadata else 'Structured Database',
                    "page": course.source_metadata.get('sheet_name', '') if course.source_metadata else '',
                    "metadata": course.source_metadata
                })
                
        # Check if this session has uploaded documents
        is_document_rag = False
        uploaded_evidence = []
        if session_id:
            from advisor.models import UploadedDocumentChunk
            is_document_rag = UploadedDocumentChunk.objects.filter(document__session_id=session_id).exists()
            
        if is_document_rag:
            # DOCUMENT RAG MODE
            uploaded_evidence = self.retrieval_service.retrieve_session_document_evidence(user_query, session_id, top_k=5)
            all_evidence = uploaded_evidence
            
            # If no relevant chunks are found for the uploaded document query, short circuit.
            if not all_evidence:
                return self._build_response(
                    DecisionEngine.STATES.get('OUT_OF_CONTEXT', 'OUT_OF_CONTEXT'),
                    "I couldn't find relevant information in the uploaded document to answer your question.",
                    []
                )
        else:
            # NORMAL ACADEMIC RAG MODE
            all_evidence = rag_evidence + structured_evidence
        
        # If BOTH RAG and Structured DB return nothing, answer Information Unavailable immediately
        if not all_evidence:
            return self._build_response(
                DecisionEngine.STATES['INFORMATION_UNAVAILABLE'],
                "I couldn't find verified information in the available university sources for that question. Please provide the course code, programme, semester, or other relevant academic detail.",
                []
            )
        
        decision_state = None
        decision_reason = None
        
        # 3. Deterministic checking if a student is provided and question is about eligibility
        if student_id and ("ELIGIBLE" in user_query.upper() or "TAKE" in user_query.upper() or "PREREQUISITE" in user_query.upper() or "PROGRESSION" in user_query.upper()):
            for code in potential_codes:
                if AcademicDataService.get_course_info(code):
                    state, reason = DecisionEngine.check_prerequisite_eligibility(student_id, code)
                    decision_state = state
                    decision_reason = reason
                    break
                    
        # 4. Handle Missing Information deterministically
        if decision_state == DecisionEngine.STATES['NEEDS_MORE_INFORMATION']:
            return self._build_response(
                state=decision_state, 
                answer=f"I need more information to answer this. {decision_reason}", 
                evidence=all_evidence,
                missing_info=[decision_reason]
            )

        if decision_state == DecisionEngine.STATES['CONFLICTING_INFORMATION']:
            return self._build_response(
                state=decision_state, 
                answer=f"I cannot provide a definitive answer because there is conflicting information in the authoritative sources. {decision_reason}", 
                evidence=all_evidence
            )

        # Gather student data if available
        student_data = None
        if student_id:
            from students.models import Student
            try:
                stu = Student.objects.get(student_id=student_id)
                student_data = {
                    "programme": stu.programme,
                    "batch": stu.batch,
                    "current_semester": stu.current_semester,
                    "profile_completeness_status": stu.profile_completeness_status
                }
            except:
                pass

        # 5. LLM Generation
        if is_document_rag:
            prompt_version = "document_rag"
        else:
            prompt_version = os.environ.get("PROMPT_VERSION", "v4")
        prompt_builder = get_prompt_builder(prompt_version)
        prompt = prompt_builder.build_prompt(user_query, all_evidence, decision_state, decision_reason, student_data)
        
        if self.client:
            models_to_try = [
                os.environ.get('GEMINI_MODEL', 'gemini-3.8-flash'),
                'gemini-3.7-flash',
                'gemini-3.6-flash',
                'gemini-3.5-flash',
                'gemini-3.1-flash-lite',
                'gemini-flash-latest'
            ]
            
            raw_answer = None
            last_error = None
            
            for model_name in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    raw_answer = response.text
                    break  # Success, exit loop
                except Exception as e:
                    print(f"[WARN] LLM API Error with model {model_name}: {type(e).__name__} - {str(e)}")
                    last_error = e
            
            if not raw_answer:
                print(f"[ERROR] All models in fallback chain failed. Last error: {type(last_error).__name__} - {str(last_error)}")
                return self._build_response(
                    decision_state or "ERROR", 
                    "The AI service is temporarily unavailable. Please try again.", 
                    []
                )
                
            # Extract JSON if it is wrapped in markdown blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_answer, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = raw_answer

            try:
                parsed_response = json.loads(json_str)
                
                llm_state = parsed_response.get("state", "ANSWERED")
                
                # Decision Engine is absolutely authoritative.
                if decision_state and llm_state != decision_state:
                    llm_state = decision_state
                    
                return self._build_response(
                    state=llm_state,
                    answer=parsed_response.get("answer", ""),
                    reason=parsed_response.get("reason"),
                    missing_info=parsed_response.get("missing_information", []),
                    evidence=parsed_response.get("evidence", []),
                    recommendation=parsed_response.get("recommendation"),
                    uncertainty=parsed_response.get("uncertainty")
                )
                
            except json.JSONDecodeError:
                print("[ERROR] Failed to parse JSON from LLM")
                return self._build_response(
                    decision_state or "ERROR", 
                    "The AI service is temporarily unavailable. Please try again.", 
                    []
                )
        else:
            return self._build_response(
                decision_state or "ERROR", 
                "The AI generation service API key is missing. Please configure GEMINI_API_KEY.", 
                []
            )
            
    def _build_response(self, state, answer, evidence, reason=None, missing_info=None, recommendation=None, uncertainty=None):
        return {
            "state": state,
            "answer": answer,
            "reason": reason,
            "evidence": evidence,
            "missing_information": missing_info or [],
            "conflict_information": state == DecisionEngine.STATES.get('CONFLICTING_INFORMATION', 'CONFLICTING_INFORMATION'),
            "recommendation": recommendation,
            "uncertainty": uncertainty
        }

from .v1_basic import V1BasicPrompt
from .v2_structured import V2StructuredPrompt
from .v3_rag_grounded import V3RagGroundedPrompt
from .v4_full_academic import V4FullAcademicPrompt
from .document_rag import DocumentRagPrompt
from .base import AdvisorResponse

PROMPT_VERSIONS = {
    'v1': V1BasicPrompt(),
    'v2': V2StructuredPrompt(),
    'v3': V3RagGroundedPrompt(),
    'v4': V4FullAcademicPrompt(),
    'document_rag': DocumentRagPrompt()
}

def get_prompt_builder(version: str = 'v4'):
    return PROMPT_VERSIONS.get(version, PROMPT_VERSIONS['v4'])

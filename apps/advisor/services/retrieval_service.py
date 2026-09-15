import math
from rag.models import DocumentChunk
from google import genai
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.client = genai.Client()
        self.model_name = "gemini-embedding-2"
        # Minimum threshold to avoid hallucinating evidence. Set based on test performance.
        self.threshold = 0.50

    def _cosine_similarity(self, vec_a, vec_b):
        if not vec_a or not vec_b:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        
        if norm_a > 0 and norm_b > 0:
            return dot_product / (norm_a * norm_b)
        return 0.0

    def retrieve_evidence(self, query, top_k=3):
        try:
            # 1. Embed the query
            res = self.client.models.embed_content(
                model=self.model_name,
                contents=query
            )
            query_embedding = res.embeddings[0].values
            
            # 2. Fetch all embedded chunks
            chunks = DocumentChunk.objects.filter(embedding__isnull=False)
            
            # 3. Score chunks
            scored_chunks = []
            for chunk in chunks:
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                scored_chunks.append((similarity, chunk))
                
            # 4. Sort and filter
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            
            evidence_list = []
            for score, chunk in scored_chunks[:top_k]:
                # Require sufficient confidence to act as evidence
                if score < self.threshold:
                    continue
                    
                evidence = {
                    "content": chunk.content,
                    "source": chunk.document.filename,
                    "page": chunk.page_number,
                    "section": chunk.section,
                    "metadata": chunk.metadata,
                    "score": score,
                    "chunk_hash": chunk.chunk_hash
                }
                evidence_list.append(evidence)
                
            return evidence_list
            
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

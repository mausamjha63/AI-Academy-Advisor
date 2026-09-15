from django.test import TestCase
from advisor.services.retrieval_service import RetrievalService
from rag.models import AcademicDocument, DocumentChunk
from unittest.mock import patch, MagicMock

class RetrievalServiceTest(TestCase):
    def setUp(self):
        self.service = RetrievalService()
        doc = AcademicDocument.objects.create(filename="Test.pdf")
        DocumentChunk.objects.create(document=doc, content="Alpha", chunk_hash="1", embedding=[1.0, 0.0, 0.0])
        DocumentChunk.objects.create(document=doc, content="Beta", chunk_hash="2", embedding=[0.0, 1.0, 0.0])
        DocumentChunk.objects.create(document=doc, content="Gamma", chunk_hash="3", embedding=[0.707, 0.707, 0.0])

    def test_cosine_similarity(self):
        sim = self.service._cosine_similarity([1, 0, 0], [1, 0, 0])
        self.assertAlmostEqual(sim, 1.0)
        sim = self.service._cosine_similarity([1, 0, 0], [0, 1, 0])
        self.assertAlmostEqual(sim, 0.0)
        sim = self.service._cosine_similarity([1, 0, 0], [0.707, 0.707, 0])
        self.assertAlmostEqual(sim, 0.707, places=3)
        sim = self.service._cosine_similarity([0, 0, 0], [1, 0, 0])
        self.assertEqual(sim, 0.0)

    @patch('google.genai.Client')
    def test_retrieve_evidence(self, mock_client):
        instance = mock_client.return_value
        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=[1.0, 0.0, 0.0])]
        instance.models.embed_content.return_value = mock_response
        self.service.client = instance
        
        evidence = self.service.retrieve_evidence("Test query", top_k=2)
        
        self.assertEqual(len(evidence), 2)
        self.assertEqual(evidence[0]['content'], "Alpha")
        self.assertEqual(evidence[1]['content'], "Gamma")
        
        # Test missing threshold (below 0.50)
        # Beta is 0.0 similarity, so it shouldn't be included even if top_k=3
        evidence_3 = self.service.retrieve_evidence("Test query", top_k=3)
        self.assertEqual(len(evidence_3), 2)

from django.test import TestCase
from rag.models import AcademicDocument, DocumentChunk

class RAGTests(TestCase):
    def test_academic_document_model(self):
        doc = AcademicDocument.objects.create(
            filename="Test.pdf",
            source_type="regulation",
            document_type="PDF"
        )
        self.assertEqual(doc.filename, "Test.pdf")
        
        chunk = DocumentChunk.objects.create(
            document=doc,
            content="Test content",
            chunk_hash="abc123hash",
            page_number=1,
            embedding=[0.1, 0.2, 0.3]
        )
        self.assertEqual(chunk.document, doc)
        self.assertEqual(chunk.embedding, [0.1, 0.2, 0.3])

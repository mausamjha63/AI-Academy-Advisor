from django.db import models

class AcademicDocument(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    source_type = models.CharField(max_length=100) # e.g. 'regulation', 'sop'
    document_type = models.CharField(max_length=50) # e.g. 'PDF', 'Excel'
    date_ingested = models.DateTimeField(auto_now_add=True)
    source_path = models.CharField(max_length=500, null=True, blank=True)
    
    def __str__(self):
        return self.filename

class DocumentChunk(models.Model):
    document = models.ForeignKey(AcademicDocument, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    section = models.CharField(max_length=255, null=True, blank=True)
    chunk_hash = models.CharField(max_length=64, unique=True)
    vector_id = models.CharField(max_length=100, null=True, blank=True)
    embedding = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.document.filename} - Page {self.page_number} ({self.chunk_hash[:8]})"

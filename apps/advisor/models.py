from django.db import models

class ChatSession(models.Model):
    title = models.CharField(max_length=255, default="New Academic Chat")
    student_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.student_id or 'General'}"

class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.JSONField(help_text="Stores user text or structured assistant JSON")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} at {self.timestamp}"

import os
import time
from django.core.management.base import BaseCommand
from rag.models import DocumentChunk
from google import genai
from google.genai import errors

class Command(BaseCommand):
    help = 'Generate embeddings for DocumentChunks using Gemini'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing embeddings',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        chunks = DocumentChunk.objects.all()
        if not force:
            chunks = chunks.filter(embedding__isnull=True)
            
        total_chunks = DocumentChunk.objects.count()
        already_embedded = total_chunks - chunks.count() if not force else 0
        remaining = chunks.count()
        
        self.stdout.write(f"Total chunks: {total_chunks}")
        self.stdout.write(f"Already embedded: {already_embedded}")
        self.stdout.write(f"Remaining to process: {remaining}")
        
        if remaining == 0:
            self.stdout.write(self.style.SUCCESS("All chunks already have embeddings."))
            return
            
        client = genai.Client()
        model_name = "gemini-embedding-2"
        
        success_count = 0
        fail_count = 0
        
        batch_size = 50
        chunk_list = list(chunks)
        
        for i in range(0, len(chunk_list), batch_size):
            batch = chunk_list[i:i + batch_size]
            contents = [c.content for c in batch]
            
            try:
                self.stdout.write(f"Processing batch {i//batch_size + 1}...")
                res = client.models.embed_content(
                    model=model_name,
                    contents=contents
                )
                
                for idx, chunk in enumerate(batch):
                    chunk.embedding = res.embeddings[idx].values
                    chunk.save(update_fields=['embedding'])
                    success_count += 1
                
                time.sleep(1) # rate limit protection
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to embed batch: {e}"))
                fail_count += len(batch)
                
        self.stdout.write(self.style.SUCCESS(f"Successfully embedded: {success_count}"))
        if fail_count > 0:
            self.stderr.write(self.style.ERROR(f"Failed: {fail_count}"))

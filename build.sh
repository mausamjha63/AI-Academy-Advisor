#!/bin/bash
# Install dependencies
pip install -r requirements.txt

# Run migrations and initialize data
python manage.py migrate
python manage.py import_academic_data
python manage.py load_synthetic_students
python manage.py loaddata fixtures/rag_fixture.json

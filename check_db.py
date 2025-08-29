import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdf_summarizer.settings')
django.setup()

# Import Django models
from django.db import connection

# Function to check if a table exists
def check_table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = %s
        """, [table_name])
        return cursor.fetchone()[0] > 0

# Check for ImageDocument table
image_table_exists = check_table_exists('summarizer_imagedocument')
print(f"ImageDocument table exists: {image_table_exists}")

# List all tables in the database
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE()
    """)
    tables = cursor.fetchall()
    print("\nAll tables in database:")
    for table in tables:
        print(f"- {table[0]}")

# Check migration history
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT app, name, applied 
        FROM django_migrations 
        WHERE app = 'summarizer' 
        ORDER BY applied
    """)
    migrations = cursor.fetchall()
    print("\nMigration history for 'summarizer' app:")
    for migration in migrations:
        print(f"- {migration[0]}.{migration[1]} applied at {migration[2]}")
#!/usr/bin/env python
import os
import sys

# Add the Django project to the path
sys.path.insert(0, '.')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizz_app.settings')

try:
    import django
    print("✓ Django imported successfully")
    
    django.setup()
    print("✓ Django setup completed")
    
    # Test importing our views
    from quizzes import views
    print("✓ Views imported successfully")
    
    # Test importing models
    from quizzes import models
    print("✓ Models imported successfully")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
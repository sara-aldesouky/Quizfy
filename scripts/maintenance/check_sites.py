import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizz_app.settings")
django.setup()

from django.contrib.sites.models import Site

print("\n=== Configured Sites ===")
for s in Site.objects.all():
    print(f"Site ID {s.id}: {s.domain} ({s.name})")

if not Site.objects.exists():
    print("No sites found! Creating default site...")
    site = Site.objects.create(domain="example.com", name="Example")
    print(f"Created: {site.domain}")

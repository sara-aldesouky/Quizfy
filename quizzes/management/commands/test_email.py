from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = "Test email configuration and password reset setup"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n=== EMAIL CONFIGURATION TEST ===\n"))
        
        # Check email settings
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"EMAIL_HOST_PASSWORD: {'SET' if settings.EMAIL_HOST_PASSWORD else 'NOT SET (will use console)'}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}\n")
        
        # Check Sites framework
        self.stdout.write(self.style.SUCCESS("=== SITES FRAMEWORK ===\n"))
        self.stdout.write(f"SITE_ID: {settings.SITE_ID}")
        
        try:
            sites = Site.objects.all()
            if sites.exists():
                for site in sites:
                    self.stdout.write(f"[OK] Site ID {site.id}: {site.domain} ({site.name})")
            else:
                self.stdout.write(self.style.WARNING("[WARN] No sites configured! Creating default..."))
                site = Site.objects.create(domain="localhost:8000", name="Local")
                self.stdout.write(f"[OK] Created Site ID {site.id}: {site.domain}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] Error checking sites: {e}"))
            
        # Test sending email
        self.stdout.write(self.style.SUCCESS("\n=== SENDING TEST EMAIL ===\n"))
        try:
            send_mail(
                subject="Quizfy Email Test",
                message="If you're reading this, email is working correctly!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["test@example.com"],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("[OK] Test email sent successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] Error sending email: {type(e).__name__}: {e}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

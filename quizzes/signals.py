"""
Signals to handle site configuration and other app-level setup
"""
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_default_site(sender, **kwargs):
    """
    After migrations run, ensure we have a proper Site configured.
    This is needed for password reset emails to work correctly.
    """
    if sender.name == 'django.contrib.sites':
        try:
            # Get or create the default site
            site = Site.objects.get_or_create(
                pk=1,
                defaults={
                    'domain': 'example.com',
                    'name': 'Quizfy Platform'
                }
            )[0]
            
            logger.info(f"[SITE] Site configured: {site.domain} ({site.name})")
        except Exception as e:
            logger.error(f"[SITE] Error creating site: {e}")

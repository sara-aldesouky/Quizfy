from django.apps import AppConfig


class QuizzesConfig(AppConfig):
    name = 'quizzes'
    
    def ready(self):
        """Initialize app and register signals"""
        import quizzes.signals  # Register post_migrate signal

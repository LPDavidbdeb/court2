from django.apps import AppConfig

class CaseManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'case_manager'

    def ready(self):
        # Import signals to ensure they are registered
        import case_manager.signals

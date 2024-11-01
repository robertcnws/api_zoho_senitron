from django.apps import AppConfig


class ApiSenitronConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_senitron'
    
    def ready(self):
        import api_senitron.signals

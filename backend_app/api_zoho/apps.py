from django.apps import AppConfig


class ApiZohoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_zoho'
    
    def ready(self):
        import api_zoho.signals
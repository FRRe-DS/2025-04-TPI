from django.apps import AppConfig


class LoginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.modulos.login'

    def ready(self):
        import apps.modulos.login.signals

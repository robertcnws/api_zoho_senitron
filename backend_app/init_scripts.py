import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_api_zoho_senitron.settings')
django.setup()

from django.core.management import call_command
from api_zoho.models import LoginUser

def create_superuser():
    username = os.getenv('DJANGO_SUPERUSER_USERNAME')
    email = os.getenv('DJANGO_SUPERUSER_EMAIL')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

    if not LoginUser.objects.filter(username=username).exists():
        print("Creating superuser...")
        call_command('createsuperuser', '--noinput', '--username', username)
        user = LoginUser.objects.get(username=username)
        user.set_password(password)
        user.email = email
        user.save()
        print("Superuser created!")

def create_loginuser():
    username = os.getenv('LOGINUSER_USERNAME')
    email = os.getenv('LOGINUSER_EMAIL')
    password = os.getenv('LOGINUSER_PASSWORD')

    if not LoginUser.objects.filter(username=username).exists():
        print("Creating LoginUser...")
        LoginUser.objects.create_user(username=username, email=email, password=password, is_staff=True)
        print("LoginUser created!")

if __name__ == "__main__":
    create_superuser()
    create_loginuser()

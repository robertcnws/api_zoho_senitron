from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import AppConfig

class ApiZohoForm(forms.ModelForm):
    class Meta:
        model = AppConfig
        fields = ['zoho_client_id', 'zoho_client_secret','zoho_redirect_uri', 'zoho_org_id']


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    
class AppConfigForm(forms.ModelForm):
    class Meta:
        model = AppConfig
        fields = [
            'zoho_client_id',
            'zoho_client_secret',
            'zoho_redirect_uri',
            'zoho_org_id',
        ]
        
        widgets = {
            'zoho_client_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zoho Client ID'}),
            'zoho_redirect_uri': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zoho Redirect URI'}),
            'zoho_org_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zoho Organization ID'}),
            'qb_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'QB Username'}),
        } 
          
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zoho_client_secret'].required = True
        self.fields['zoho_client_id'].required = True
        self.fields['zoho_redirect_uri'].required = True
        self.fields['zoho_org_id'].required = True

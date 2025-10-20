# serializers.py
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

def _parse_bool(value):
    if isinstance(value, bool): return value
    if isinstance(value, (int, float)): return bool(value)
    if isinstance(value, str): return value.strip().lower() in {"1","true","yes","y","si","sí"}
    return False

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        remember_me = _parse_bool(self.context['request'].data.get('rememberMe', False))
        refresh = RefreshToken.for_user(self.user)
        
        if remember_me:
            access_lt  = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME_REMEMBER")
            refresh_lt = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME_REMEMBER")
        else:
            access_lt  = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME")
            refresh_lt = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
        
        if refresh_lt:
            refresh.set_exp(lifetime=refresh_lt)
        access = refresh.access_token
        if access_lt:
            access.set_exp(lifetime=access_lt)
        
        refresh['remember'] = bool(remember_me)

        data['access'] = str(access)
        data['refresh'] = str(refresh)
        data['rememberMe'] = bool(remember_me)
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Respeta el claim 'remember' del refresh para recalcular el exp del nuevo access.
    Si ROTATE_REFRESH_TOKENS=True y quieres extender también el refresh,
    vuelve a emitirlo aplicando el lifetime correspondiente y preserva 'remember'.
    """
    def validate(self, attrs):
        refresh = RefreshToken(attrs['refresh'])
        remember = bool(refresh.get('remember', False))

        from django.conf import settings
        if remember:
            access_lt  = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME_REMEMBER")
        else:
            access_lt  = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME")

        access = refresh.access_token
        if access_lt:
            access.set_exp(lifetime=access_lt)

        data = {'access': str(access)}
        
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
            new_refresh = RefreshToken.for_user(refresh.user)
            
            new_refresh['remember'] = remember
            refresh_lt = (settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME_REMEMBER")
                          if remember else settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME"))
            if refresh_lt:
                new_refresh.set_exp(lifetime=refresh_lt)
            data['refresh'] = str(new_refresh)

        return data

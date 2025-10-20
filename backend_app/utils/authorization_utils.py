from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}
    return False

def _mint_tokens(user, remember_me: bool):
    """
    Emite tokens con expiración dinámica.
    """
    
    if remember_me:
        access_lt  = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME_REMEMBER")
        refresh_lt = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME_REMEMBER")
    else:
        access_lt  = settings.SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME")
        refresh_lt = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
    
    refresh = RefreshToken.for_user(user)
    if refresh_lt:
        refresh.set_exp(lifetime=refresh_lt)  
    
    access = refresh.access_token
    if access_lt:
        access.set_exp(lifetime=access_lt) 

    return str(access), str(refresh), access_lt, refresh_lt
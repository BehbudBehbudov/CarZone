import jwt
from django.conf import settings
from django.contrib.auth.models import User
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs


class JWTAuthMiddleware(BaseMiddleware):
    """
    WebSocket üçün JWT token authentication middleware
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # WebSocket bağlantısında headers və query parametrləri yoxla
        if scope["type"] == "websocket":
            # Query parametrlərindən token al
            query_string = scope.get("query_string", b"").decode()
            token = None

            if query_string:
                try:
                    query_params = parse_qs(query_string)
                    if "token" in query_params:
                        token = query_params["token"][0]
                except:
                    pass

            # Headers-dən token al (Authorization header)
            if not token:
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization", b"").decode()
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]

            # Token mövcud olan halda authenticate et
            if token:
                try:
                    # Token-i yoxla
                    access_token = AccessToken(token)
                    user_id = access_token.payload.get('user_id')

                    if user_id:
                        user = await self.get_user_by_id(user_id)
                        if user:
                            scope["user"] = user
                        else:
                            scope["user"] = None
                    else:
                        scope["user"] = None

                except (InvalidToken, TokenError, ValueError):
                    scope["user"] = None
            else:
                scope["user"] = None

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """
        ID ilə istifadəçi tap
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
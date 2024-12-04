import json
import logging
from datetime import datetime
from typing import Optional

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

from Authentication.kafka_producer import send_event_to_kafka

logger = logging.getLogger(__name__)


def send_kafka_event(event_type: str, username: str) -> None:
    """Отправляет событие в Kafka."""
    event = {
        "event_type": event_type,
        "username": username,
        "timestamp": datetime.utcnow().isoformat(),
    }
    try:
        send_event_to_kafka("user-events", json.dumps(event))
        logger.info(f"Событие {event_type} отправлено в Kafka: {username}.")
    except Exception as e:
        logger.error(f"Ошибка отправки события {event_type} в Kafka: {e}")


class RegisterView(APIView):
    """Обрабатывает регистрацию нового пользователя."""

    def post(self, request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            logger.warning("Попытка регистрации без указания имени пользователя или пароля.")
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            logger.warning(f"Попытка регистрации с существующим именем пользователя: {username}.")
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(username=username, password=password)
            logger.info(f"Новый пользователь зарегистрирован: {username}.")
            send_kafka_event("user_registration", username)
            return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {username}: {e}")
            return Response({"error": "Error creating user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    """Обрабатывает вход пользователя."""

    def post(self, request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if not user:
            logger.warning(f"Неудачная попытка входа для пользователя: {username}.")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        response = Response({"message": "Login successful"})
        response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True, samesite="Strict")
        response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, samesite="Strict")

        send_kafka_event("user_login", username)
        return response


class LogoutView(APIView):
    """Обрабатывает выход пользователя."""

    def post(self, request) -> Response:
        response = Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        username: Optional[str] = None
        access_token = request.COOKIES.get("access_token")
        if access_token:
            try:
                token = AccessToken(access_token)
                user_id = token.get("user_id")
                username = User.objects.get(id=user_id).username
                logger.info(f"Пользователь {username} успешно извлечен из токена.")
            except Exception as e:
                logger.warning(f"Ошибка при извлечении пользователя из токена: {e}")

        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"Refresh-токен добавлен в черный список для пользователя {username}.")
            except InvalidToken:
                logger.warning("Попытка выхода с недействительным refresh_token.")

        if username:
            send_kafka_event("user_logout", username)
        else:
            logger.info("Событие выхода не отправлено, так как пользователь не аутентифицирован.")

        return response


class RefreshTokenView(APIView):
    """Обрабатывает обновление токена доступа."""

    def post(self, request) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            logger.warning("Попытка обновления токена без refresh_token.")
            return Response({"error": "Refresh token not found"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            response = Response({"message": "Token refreshed"})
            response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True,
                                samesite="Strict")
            logger.info("Токен доступа успешно обновлен.")
            return response
        except InvalidToken:
            logger.warning("Обновление токена не удалось: недействительный refresh_token.")
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError:
            return Response({'error': 'Недействительный или истекший refresh-токен'}, status=401)

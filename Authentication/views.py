import json
import logging
from datetime import datetime

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from Authentication.kafka_producer import send_event_to_kafka

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    Обрабатывает регистрацию нового пользователя.
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            logger.warning("Попытка регистрации без username или password.")
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            logger.warning(f"Попытка регистрации с существующим username: {username}.")
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(username=username, password=password)
            logger.info(f"Пользователь создан: {username}.")
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {username}: {e}")
            return Response({"error": "Error creating user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Отправляем событие в Kafka
        event = {
            "event_type": "user_registration",
            "username": username,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            send_event_to_kafka("user-events", json.dumps(event))
            logger.info("Событие регистрации отправлено в Kafka.")
        except Exception as e:
            logger.error(f"Ошибка отправки события в Kafka: {e}")

        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Обрабатывает вход пользователя.
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is None:
            logger.warning(f"Неудачная попытка входа: {username}.")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({"message": "Login successful"})
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Strict'
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='Strict'
        )

        # Отправляем событие в Kafka
        event = {
            "event_type": "user_login",
            "username": username,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            send_event_to_kafka("user-events", json.dumps(event))
            logger.info(f"Событие входа отправлено в Kafka: {username}.")
        except Exception as e:
            logger.error(f"Ошибка отправки события входа в Kafka: {e}")

        return response


class LogoutView(APIView):
    """
    Обрабатывает выход пользователя.
    """
    def post(self, request):
        response = Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"Токен добавлен в черный список для пользователя: {request.user.username}.")
            except InvalidToken:
                logger.warning("Попытка выхода с недействительным токеном.")

        # Отправляем событие в Kafka
        event = {
            "event_type": "user_logout",
            "username": request.user.username if request.user.is_authenticated else "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            send_event_to_kafka("user-events", json.dumps(event))
            logger.info(f"Событие выхода отправлено в Kafka: {event['username']}.")
        except Exception as e:
            logger.error(f"Ошибка отправки события выхода в Kafka: {e}")

        return response


class RefreshTokenView(APIView):
    """
    Обрабатывает обновление токена доступа.
    """
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            logger.warning("Попытка обновления токена без refresh_token.")
            return Response({"error": "Refresh token not found"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            response = Response({"message": "Token refreshed"})
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            logger.info("Токен успешно обновлен.")
            return response
        except InvalidToken:
            logger.warning("Попытка обновления с недействительным refresh_token.")
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

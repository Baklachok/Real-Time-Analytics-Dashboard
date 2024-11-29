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
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password)

        # Отправляем событие в Kafka
        event = {
            "event_type": "user_registration",
            "username": username,
            "timestamp": str(datetime.now())
        }

        logger.debug("Attempting to send Kafka event...")
        send_event_to_kafka("user-events", json.dumps(event))
        logger.info("Kafka event sent.")

        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except InvalidToken:
                pass

        # Отправляем событие в Kafka
        event = {
            "event_type": "user_logout",
            "username": request.user.username if request.user.is_authenticated else "unknown",
            "timestamp": str(datetime.now())
        }
        send_event_to_kafka("user-events", json.dumps(event))

        return response



class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({"message": "Login successful"})
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,  # Только для серверного доступа
            secure=True,    # Только через HTTPS (в продакшене)
            samesite='Strict'  # Защита от CSRF
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
            "timestamp": str(datetime.now())
        }
        send_event_to_kafka("user-events", json.dumps(event))

        return response


class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
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
            return response
        except InvalidToken:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)


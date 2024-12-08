import os

import django
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytics_project.settings')
django.setup()


class AuthenticationTests(APITestCase):
    def test_register_user(self):
        """Тест успешной регистрации пользователя"""
        response = self.client.post('/api/auth/register/', {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_existing_user(self):
        """Тест регистрации с существующим именем пользователя"""
        User.objects.create_user(username='testuser', password='testpassword')
        response = self.client.post('/api/auth/register/', {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_without_username(self):
        """Тест регистрации без указания имени пользователя"""
        response = self.client.post('/api/auth/register/', {'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_register_user_without_password(self):
        """Тест регистрации без указания пароля"""
        response = self.client.post('/api/auth/register/', {'username': 'testuser'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_login_user(self):
        """Тест успешного входа"""
        User.objects.create_user(username='testuser', password='testpassword')
        response = self.client.post('/api/auth/login/', {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)

    def test_invalid_login(self):
        """Тест входа с неверными данными"""
        response = self.client.post('/api/auth/login/', {'username': 'nonexistent', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_with_wrong_password(self):
        """Тест входа с неверным паролем"""
        User.objects.create_user(username='testuser', password='correctpassword')
        response = self.client.post('/api/auth/login/', {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_user_with_missing_credentials(self):
        """Тест входа без указания имени пользователя или пароля"""
        response = self.client.post('/api/auth/login/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_logout_user(self):
        """Тест успешного выхода пользователя"""
        user = User.objects.create_user(username='testuser', password='testpassword')
        refresh = RefreshToken.for_user(user)
        self.client.cookies['access_token'] = str(refresh.access_token)
        self.client.cookies['refresh_token'] = str(refresh)

        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_refresh_token_success(self):
        """Тест успешного обновления токена доступа"""
        user = User.objects.create_user(username='testuser', password='testpassword')
        refresh = RefreshToken.for_user(user)
        self.client.cookies['refresh_token'] = str(refresh)

        response = self.client.post('/api/auth/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)

    def test_refresh_token_invalid(self):
        """Тест обновления токена с недействительным refresh_token"""
        # Используем заведомо некорректный JWT токен
        invalid_refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.InvalidPayload.Signature"
        self.client.cookies['refresh_token'] = invalid_refresh_token

        response = self.client.post('/api/auth/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_refresh_token_missing(self):
        """Тест обновления токена без refresh_token"""
        response = self.client.post('/api/auth/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

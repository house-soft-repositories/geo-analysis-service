"""
Backend de autenticação que delega a verificação ao backend NestJS.

Fluxo:
  1. POST {NESTJS_BACKEND_URL}/api/auth/login  → obtém access token
  2. GET  {NESTJS_BACKEND_URL}/api/auth/me     → obtém dados do usuário (incluindo role)
  3. Cria/atualiza um User Django espelho, concedendo is_staff/is_superuser para ADMIN.

Apenas usuários com role == "ADMIN" recebem acesso ao Django Admin.
"""

import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

logger = logging.getLogger(__name__)

User = get_user_model()

NESTJS_ADMIN_ROLE = "ADMIN"
REQUEST_TIMEOUT = 10  # segundos


def _nestjs_url(path: str) -> str:
    base = getattr(settings, "NESTJS_BACKEND_URL", "http://localhost:3000").rstrip("/")
    return f"{base}{path}"


class NestJsAuthBackend(BaseBackend):
    """
    Autentica usuários do Django Admin verificando as credenciais
    contra o backend NestJS (POST /api/auth/login).

    Somente usuários com role ADMIN no NestJS recebem is_staff=True
    e is_superuser=True, podendo assim acessar o Django Admin.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # 1. Login no NestJS
        try:
            login_resp = requests.post(
                _nestjs_url("/api/auth/login"),
                json={"email": username, "password": password},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning("NestJsAuthBackend: falha ao contatar NestJS – %s", exc)
            return None

        if login_resp.status_code not in (200, 201):
            return None

        token_data = login_resp.json()
        access_token = token_data.get("accessToken")
        if not access_token:
            return None

        # 2. Busca dados do usuário no NestJS
        try:
            me_resp = requests.get(
                _nestjs_url("/api/auth/me"),
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning("NestJsAuthBackend: falha ao buscar /me – %s", exc)
            return None

        if me_resp.status_code != 200:
            return None

        user_data = me_resp.json()
        role = user_data.get("role", "")
        is_admin = role == NESTJS_ADMIN_ROLE

        # Apenas ADMINs acessam o Django Admin
        if not is_admin:
            return None

        # 3. Cria ou atualiza o User Django espelho
        email = user_data.get("email", username)
        name = user_data.get("name", "")
        first_name, _, last_name = name.partition(" ")

        # username no Django tem limite de 150 caracteres
        django_username = email[:150]

        user, created = User.objects.get_or_create(
            username=django_username,
            defaults={"email": email, "first_name": first_name, "last_name": last_name},
        )

        if not created:
            # Atualiza campos caso tenham mudado no NestJS
            user.email = email
            user.first_name = first_name
            user.last_name = last_name

        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        # A senha é gerenciada pelo NestJS; impede login direto via senha Django
        user.set_unusable_password()
        user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

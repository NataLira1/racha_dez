import pytest

from app.api.models import user
from app.api.models.user import User, Occupation
from app.core.security import get_password_hash
from app.tests.api.base import client, db_session, setup_db
from app.api.utils.utils import generate_password_reset_token

LOGIN_PREFIX = "/v1/login"


@pytest.fixture
def setup_admin_user(db_session, client):
    user = User(
        full_name="Administrador",
        email="admin@example.ufcg.edu.br",
        cpf="12345678901",
        phone="83911223344",
        occupation=Occupation.SERVIDOR,
        hashed_password=get_password_hash(password="admin password"),
        is_active=True,
        is_admin=True,
        is_internal=True,
        reservations=[],
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def set_up_user(db_session, client):
    user = User(
        full_name="Francisnaldo",
        email="francisnaldo@example.ufcg.edu.br",
        cpf="12345678123",
        phone="83911223344",
        occupation=Occupation.ALUNO,
        hashed_password=get_password_hash(password="francisnaldo password"),
        is_active=False,
        is_admin=False,
        is_internal=True,
        reservations=[],
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def admin_access_token(client, setup_admin_user):
    response = client.post(
        "/v1/login/access-token",
        data={
            "username": setup_admin_user.email,
            "password": "admin password",
        },
    )

    return response.json()["access_token"]


@pytest.fixture
def user_access_token(db_session, client):
    user = User(
        full_name="João",
        email="joao@example.ufcg.edu.br",
        cpf="12345678123",
        phone="83911223344",
        occupation=Occupation.ALUNO,
        hashed_password=get_password_hash(password="joao password"),
        is_active=True,
        is_admin=False,
        is_internal=True,
        reservations=[],
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        "/v1/login/access-token",
        data={
            "username": "joao@example.ufcg.edu.br",
            "password": "joao password",
        },
    )

    return response.json()["access_token"]


class TestRoutesLogin:
    def test_login_access_success(self, client, setup_admin_user):
        response = client.post(
            "/v1/login/access-token",
            data={
                "username": setup_admin_user.email,
                "password": "admin password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200

    def test_login_access_incorrect_email(self, client, setup_admin_user):
        response = client.post(
            "/v1/login/access-token",
            data={
                "username": "emailerrado@example.ufcg.edu.br",
                "password": "admin password",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 400, response.text
        assert response.json()["detail"] == "Email ou senha incorretos."

    def test_login_access_incorrect_password(self, client, setup_admin_user):
        response = client.post(
            "/v1/login/access-token",
            data={
                "username": setup_admin_user.email,
                "password": "senha incorreta",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 400, response.text
        assert response.json()["detail"] == "Email ou senha incorretos."

    def test_confirm_email(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        first_response = client.get(
            LOGIN_PREFIX + f"/confirm-email/{admin_access_token}"
        )
        second_response = client.get(
            LOGIN_PREFIX + f"/confirm-email/{user_access_token}"
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 200

        assert first_response.json()["email"] == setup_admin_user.email
        assert second_response.json()["email"] == "joao@example.ufcg.edu.br"

    def test_confirm_email_with_incorrect_token(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        first_response = client.get(LOGIN_PREFIX + f"/confirm-email/token incorreto")
        second_response = client.get(LOGIN_PREFIX + f"/confirm-email/token incorreto")

        assert first_response.status_code == 400
        assert second_response.status_code == 400

    def test_login_test_token(self, client, admin_access_token):
        response = client.post(
            "/v1/login/test-token",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 200
        json_data = response.json()

        assert json_data["email"] == "admin@example.ufcg.edu.br"
        assert json_data["full_name"] == "Administrador"
        assert json_data["is_active"] is True

    def test_login_test_token_with_incorrect_token(self, client, admin_access_token):
        response = client.post(
            "/v1/login/test-token", headers={"Authorization": f"Bearer token incorreto"}
        )

        assert response.status_code == 403
        json_data = response.json()

        assert json_data["detail"] == "Não foi possível validar as credenciais"

    def test_password_recovery_existing_email(self, client, setup_admin_user):
        response = client.post(f"/v1/password-recovery/{setup_admin_user.email}")

        assert response.status_code == 200
        assert response.json() == "Email de recuperação de senha enviado."

    def test_password_recovery_incorrect_email(self, client, setup_admin_user):
        response = client.post(f"/v1/password-recovery/email incorreto")

        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "Não existe um usuário com esse email no sistema."
        )

    def test_reset_password(self, client, setup_admin_user):
        token = generate_password_reset_token(email=setup_admin_user.email)

        data = {"token": token, "new_password": "nova senha"}
        response = client.post("/v1/reset-password/", json=data)

        assert response.status_code == 200
        assert response.json() == "Senha atualizada com sucesso."

        response_login = client.post(
            "/v1/login/access-token",
            data={
                "username": setup_admin_user.email,
                "password": "nova senha",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response_login.status_code == 200

    def test_reset_password_with_incorrect_email(self, client, setup_admin_user):
        token = generate_password_reset_token(email="email incorreto")

        data = {"token": token, "new_password": "nova senha"}
        response = client.post("/v1/reset-password/", json=data)

        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "Não existe um usuário com esse email no sistema."
        )

    def test_reset_password_with_invalid_token(self, client, setup_admin_user):
        token = "Token inválido"

        data = {"token": token, "new_password": "nova senha"}
        response = client.post("/v1/reset-password/", json=data)

        assert response.status_code == 400
        assert response.json()["detail"] == "Token inválido."

    def test_reset_password_inactive_user(self, client, set_up_user):
        token = generate_password_reset_token(email=set_up_user.email)

        data = {"token": token, "new_password": "nova senha"}
        response = client.post("/v1/reset-password/", json=data)

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Usuário inativo. Por favor, verifique seu e-mail para confirmar o seu cadastro."
        )

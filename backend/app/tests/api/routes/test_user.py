import pytest
import uuid

from app.api.models import user
from app.api.models.user import User, Occupation
from app.core.security import get_password_hash
from app.tests.api.base import client, db_session, setup_db


USER_PREFIX = "/v1/users"


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
        full_name="Francisnaldo",
        email="francisnaldo@example.ufcg.edu.br",
        cpf="12345678123",
        phone="83911223344",
        occupation=Occupation.ALUNO,
        hashed_password=get_password_hash(password="francisnaldo password"),
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
            "username": "francisnaldo@example.ufcg.edu.br",
            "password": "francisnaldo password",
        },
    )

    return response.json()["access_token"]


class TestUserRoutes:
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

    def test_get_users(self, client, setup_admin_user, admin_access_token):
        response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert response.status_code == 200
        assert response.json()[0]["email"] == "admin@example.ufcg.edu.br"

    def test_get_users_without_privileges(
        self, client, setup_admin_user, user_access_token
    ):
        response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {user_access_token}"}
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "O usuário não tem privilégios suficientes"

    def test_get_user_by_id(self, client, setup_admin_user, admin_access_token):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        first_user_id = get_users_response.json()[0]["id"]

        assert get_users_response.status_code == 200
        response = client.get(
            USER_PREFIX + f"/{first_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 200

    def test_get_user_by_id_without_privileges(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        first_user_id = get_users_response.json()[0]["id"]

        assert get_users_response.status_code == 200
        response = client.get(
            USER_PREFIX + f"/{first_user_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 403
        assert (
            response.json()["detail"] == "O usuário não tem permissão de administrador."
        )

    def test_get_user_by_email(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        first_user_email = get_users_response.json()[0]["email"]
        second_user_email = get_users_response.json()[1]["email"]

        first_response = client.get(
            USER_PREFIX + f"/email/{first_user_email}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert first_response.status_code == 200

        second_response = client.get(
            USER_PREFIX + f"/email/{second_user_email}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert second_response.status_code == 200

    def test_get_user_by_email_not_exists(
        self, client, setup_admin_user, admin_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        response = client.get(
            USER_PREFIX + "/email/fake_email@example.ufcg.edu.br",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Usuário não encontrado."

    def test_get_user_by_email_without_privileges(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        first_user_email = get_users_response.json()[0]["email"]
        second_user_email = get_users_response.json()[1]["email"]

        first_response = client.get(
            USER_PREFIX + f"/email/{first_user_email}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert first_response.status_code == 403

        # On this case, the current user retrieves it's own user by his/her email
        second_response = client.get(
            USER_PREFIX + f"/email/{second_user_email}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        # So, the status code should be 200
        assert second_response.status_code == 200

    def test_get_current_user_as_admin(
        self, client, setup_admin_user, admin_access_token
    ):
        response = client.get(
            USER_PREFIX + "/me",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == setup_admin_user.email

    def test_get_current_user_as_user(
        self, client, setup_admin_user, user_access_token
    ):
        response = client.get(
            USER_PREFIX + "/me",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == "francisnaldo@example.ufcg.edu.br"

    def test_get_user_by_id_not_exists(
        self, client, setup_admin_user, admin_access_token
    ):
        random_uuid = uuid.uuid4()
        response = client.get(
            USER_PREFIX + f"/{random_uuid}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Usuário não encontrado."

    def test_create_internal_user(self, client, setup_admin_user, admin_access_token):
        data = {
            "email": "user@example.ufcg.edu.br",
            "cpf": "80513586160",
            "phone": "83999124702",
            "occupation": "ALUNO",
            "is_active": True,
            "is_admin": False,
            "is_internal": True,
            "full_name": "Internal User",
            "password": "internal user password",
        }

        response = client.post(
            USER_PREFIX + "/",
            headers={
                "Authorization": f"Bearer {admin_access_token}",
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=data,
        )

        assert response.status_code == 200

        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert len(get_users_response.json()) == 2

        second_user_id = get_users_response.json()[1]["id"]

        created = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert created.json()["email"] == data["email"]

    def test_create_internal_user_without_privileges(
        self, client, setup_admin_user, user_access_token
    ):
        data = {
            "email": "user@example.ufcg.edu.br",
            "cpf": "80513586160",
            "phone": "83999124702",
            "occupation": "ALUNO",
            "is_active": True,
            "is_admin": False,
            "is_internal": True,
            "full_name": "Internal User",
            "password": "internal user password",
        }

        response = client.post(
            USER_PREFIX + "/",
            headers={
                "Authorization": f"Bearer {user_access_token}",
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=data,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "O usuário não tem privilégios suficientes"

    def test_create_internal_user_email_already_exist(
        self, client, setup_admin_user, admin_access_token
    ):
        data = {
            "email": "user@example.ufcg.edu.br",
            "cpf": "12345678911",
            "phone": "83999124702",
            "occupation": "ALUNO",
            "is_active": True,
            "is_admin": False,
            "is_internal": True,
            "full_name": "Internal User",
            "password": "internal user password",
        }

        response = client.post(
            USER_PREFIX + "/",
            headers={
                "Authorization": f"Bearer {admin_access_token}",
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=data,
        )

        assert response.status_code == 200

        data_second_user = {
            "email": "user@example.ufcg.edu.br",
            "cpf": "12345678922",
            "phone": "83999124702",
            "occupation": "ALUNO",
            "is_active": True,
            "is_admin": False,
            "is_internal": True,
            "full_name": "Internal User",
            "password": "internal user password",
        }

        response_second_user = client.post(
            USER_PREFIX + "/",
            headers={
                "Authorization": f"Bearer {admin_access_token}",
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=data_second_user,
        )

        assert response_second_user.status_code == 400
        assert (
            response_second_user.json()["detail"]
            == "Já existe um usuário com esse e-mail."
        )

    def test_create_internal_user_cpf_already_exist(
        self, client, setup_admin_user, admin_access_token
    ):
        data = {
            "email": "user@example.ufcg.edu.br",
            "cpf": "12345678911",
            "phone": "83999124702",
            "occupation": "ALUNO",
            "is_active": True,
            "is_admin": False,
            "is_internal": True,
            "full_name": "Internal User",
            "password": "internal user password",
        }

        response = client.post(
            USER_PREFIX + "/",
            headers={
                "Authorization": f"Bearer {admin_access_token}",
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=data,
        )

        assert response.status_code == 200

        data_second_user = {
            "email": "user2@example.ufcg.edu.br",
            "cpf": "12345678911",
            "phone": "83999124702",
            "occupation": "ALUNO",
            "is_active": True,
            "is_admin": False,
            "is_internal": True,
            "full_name": "Internal User",
            "password": "internal user password",
        }

        response_second_user = client.post(
            USER_PREFIX + "/",
            headers={
                "Authorization": f"Bearer {admin_access_token}",
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=data_second_user,
        )

        assert response_second_user.status_code == 400
        assert (
            response_second_user.json()["detail"]
            == "Já existe um usuário com esse CPF."
        )

    def test_signup(self, client, setup_admin_user):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "12345678911",
            "phone": "83911223344",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 200
        assert data["email"] == response.json()["email"]
        assert "id" in response.json()

    def test_signup_user_email_already_exist(self, client, setup_admin_user):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "11111111111",
            "phone": "83911111111",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 200

        data_duplicated_email = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "22222222222",
            "phone": "83922222222",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response_duplicated_email = client.post(
            USER_PREFIX + "/signup", json=data_duplicated_email
        )

        assert response_duplicated_email.status_code == 400
        assert (
            response_duplicated_email.json()["detail"]
            == "Já existe um usuário com esse e-mail."
        )

    def test_signup_user_cpf_already_exist(self, client, setup_admin_user):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "11111111111",
            "phone": "83911111111",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 200

        data_duplicated_cpf = {
            "email": "user2@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "11111111111",
            "phone": "83922222222",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response_duplicated_cpf = client.post(
            USER_PREFIX + "/signup", json=data_duplicated_cpf
        )

        assert response_duplicated_cpf.status_code == 400
        assert (
            response_duplicated_cpf.json()["detail"]
            == "Já existe um usuário com esse CPF."
        )

    def test_signup_user_invalid_cpf(self, client):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "123456789123",  # invalid CPF (more than 11 digits)
            "phone": "83911111111",
            "occupation": "ALUNO",
            "full_name": "CPF inválido",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 422  # Validation error
        response_data = response.json()["detail"]

        assert any(
            error["loc"] == ["body", "cpf"]
            and error["msg"] == "String should have at most 11 characters"
            for error in response_data
        )

    def test_signup_user_invalid_occupation(self, client):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "123456789123",  # invalid CPF (more than 11 digits)
            "phone": "83911111111",
            "occupation": "INVALID OCCUPATION",  # invalid occupation
            "full_name": "CPF inválido",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 422

    def test_signup_user_invalid_phone(self, client):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "123456789123",  # invalid CPF (more than 11 digits)
            "phone": "83911abc111",
            "occupation": "INVALID OCCUPATION",  # invalid occupation
            "full_name": "CPF inválido",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 422

    def test_block_user_by_id(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The second user created is a normal user, and the first one is the admin himself
        second_user_id = get_users_response.json()[1]["id"]

        response = client.patch(
            f"/v1/block/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 200
        assert response.json() == {"ok": True}

        get_user_response = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

    def test_block_user_by_id_without_privileges(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The second user created is a normal user, and the first one is the admin himself
        second_user_id = get_users_response.json()[1]["id"]

        response = client.patch(
            f"/v1/block/{second_user_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "O usuário não tem privilégios suficientes"

        get_user_response = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is True

    def test_block_user_by_id_not_exists(
        self, client, setup_admin_user, admin_access_token
    ):
        random_uuid = uuid.uuid4()
        response = client.patch(
            f"/v1/block/{random_uuid}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Usuário não encontrado."

    def test_unblock_user_by_id(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The second user created is a normal user, and the first one is the admin himself
        second_user_id = get_users_response.json()[1]["id"]

        block_response = client.patch(
            f"/v1/block/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert block_response.status_code == 200
        assert block_response.json() == {"ok": True}

        get_user_response = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

        response = client.patch(
            f"/v1/unblock/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == "francisnaldo@example.ufcg.edu.br"

        get_user_response = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is True

    def test_unblock_user_by_id_without_privileges(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "12345678911",
            "phone": "83911223344",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 200

        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The third user created is a normal user, and the first one is the admin himself
        third_user_id = get_users_response.json()[2]["id"]

        block_response = client.patch(
            f"/v1/block/{third_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert block_response.status_code == 200
        assert block_response.json() == {"ok": True}

        get_user_response = client.get(
            USER_PREFIX + f"/{third_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

        response = client.patch(
            f"/v1/unblock/{third_user_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "O usuário não tem privilégios suficientes"

        get_user_response = client.get(
            USER_PREFIX + f"/{third_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

    def test_unblock_user_himself(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The second user created is a normal user, and the first one is the admin himself
        second_user_id = get_users_response.json()[1]["id"]

        block_response = client.patch(
            f"/v1/block/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert block_response.status_code == 200
        assert block_response.json() == {"ok": True}

        get_user_response = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

        response = client.patch(
            f"/v1/unblock/{second_user_id}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Usuario Inativo"

        get_user_response = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

    def test_unblock_user_by_id_not_exists(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        random_uuid = uuid.uuid4()
        block_response = client.patch(
            f"/v1/block/{random_uuid}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert block_response.status_code == 404
        assert block_response.json()["detail"] == "Usuário não encontrado."

    def test_get_blocked_users(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The second user created is a normal user, and the first one is the admin himself
        second_user_id = get_users_response.json()[1]["id"]

        block_response = client.patch(
            f"/v1/block/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert block_response.status_code == 200
        assert block_response.json() == {"ok": True}

        get_user_response = client.get(
            USER_PREFIX + f"/{second_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

        response = client.get(
            "/v1/block",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 200
        assert response.json()[0]["email"] == "francisnaldo@example.ufcg.edu.br"

    def test_get_blocked_users_without_privileges(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "12345678911",
            "phone": "83911223344",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 200

        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The third user created is a normal user, and the first one is the admin himself
        third_user_id = get_users_response.json()[2]["id"]

        block_response = client.patch(
            f"/v1/block/{third_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert block_response.status_code == 200
        assert block_response.json() == {"ok": True}

        get_user_response = client.get(
            USER_PREFIX + f"/{third_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

        response = client.get(
            "/v1/block",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "O usuário não tem privilégios suficientes"

        get_user_response = client.get(
            USER_PREFIX + f"/{third_user_id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert get_user_response.status_code == 200
        assert get_user_response.json()["is_active"] is False

    def test_get_user_id_by_email_with_privileges(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The 2nd user is a normal user, the 1st is admin
        user_id = get_users_response.json()[1]["id"]
        user_email = get_users_response.json()[1]["email"]

        assert get_users_response.status_code == 200
        response = client.get(
            USER_PREFIX + f"/user-id/{user_email}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["user_id"] == user_id

    def test_get_user_id_by_email_without_privileges(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The third user is a normal user, the 1st is the admin
        user_id = get_users_response.json()[1]["id"]
        user_email = get_users_response.json()[1]["email"]

        assert get_users_response.status_code == 200
        response = client.get(
            USER_PREFIX + f"/user-id/{user_email}",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["user_id"] == user_id

    def test_get_user_id_by_email_user_inactive(
        self, client, setup_admin_user, admin_access_token, user_access_token
    ):
        # This user is created but he's not active
        data = {
            "email": "user@ccc.ufcg.edu.br",
            "password": "senha1234",
            "cpf": "12345678911",
            "phone": "83911223344",
            "occupation": "ALUNO",
            "full_name": "user",
        }

        response = client.post(USER_PREFIX + "/signup", json=data)

        assert response.status_code == 200

        get_users_response = client.get(
            USER_PREFIX + "/", headers={"Authorization": f"Bearer {admin_access_token}"}
        )

        assert get_users_response.status_code == 200

        # The third user is the just created one, 1st is admin and 2nd is a normal user
        third_user_id = get_users_response.json()[2]["id"]
        third_user_email = get_users_response.json()[2]["email"]

        assert get_users_response.status_code == 200
        response = client.get(
            USER_PREFIX + f"/user-id/{third_user_email}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Usuário inativo ou bloqueado"

    def test_get_user_id_by_email_not_exists(
        self, client, setup_admin_user, user_access_token
    ):
        response = client.get(
            USER_PREFIX + "/user-id/fake_email@example.ufcg.edu.br",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Usuário não encontrado."

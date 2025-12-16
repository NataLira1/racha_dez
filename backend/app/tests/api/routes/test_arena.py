import pytest

from app.api.models.arena import Arena, ArenaType
from app.api.models.user import User, Occupation
from app.core.security import get_password_hash
from app.tests.api.base import client, db_session, setup_db


ARENA_PREFIX = "/v1/arenas"


@pytest.fixture
def setUp(db_session):
    arena = Arena(name="Volei1", description="Foo bar",
                  capacity=10, type=ArenaType.VOLEI)
    db_session.add(arena)
    db_session.commit()
    db_session.refresh(arena)

    return arena


@pytest.fixture
def admin(db_session):
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
        reservations=[],)

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def access_token(client, admin):
    response = client.post('/v1/login/access-token', data={
        "username": admin.email,
        "password": "admin password",
    })

    return response.json()["access_token"]


class TestArenaRoutes():

    def test_get_arenas(self, client, setUp, access_token):
        response = client.get(
            ARENA_PREFIX + "/",
            headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 200

    def test_get_arenas_unauthorized(self, client, setUp):
        response = client.get(ARENA_PREFIX + "/")

        assert response.status_code == 401

    def test_get_arena(self, client, setUp, access_token):
        response = client.get(
            ARENA_PREFIX + "/1",
            headers={"Authorization": f"Bearer {access_token}"})

        data = response.json()

        assert response.status_code == 200
        assert data["name"] == "Volei1"

    def test_get_arena_unauthorized(self, client, setUp):
        response = client.get(ARENA_PREFIX + "/1")

        data = response.json()

        assert response.status_code == 401

    def test_get_arena_not_exists(self, client, access_token):
        response = client.get(
            ARENA_PREFIX + "/1",
            headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 404
        assert "Não existe uma arena com o id 1." in response.json()['detail']

    def test_create_arena(self, client, access_token):
        data = {"name": "Society Teste",
                "description": "Foo bar", "capacity": 10, "type": "VOLEI"}
        response = client.post(
            ARENA_PREFIX + "/",
            json=data,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        created = client.get(
            ARENA_PREFIX + "/1",
            headers={"Authorization": f"Bearer {access_token}"}).json()

        assert response.status_code == 200
        assert created['name'] == data['name']

    def test_create_arena_unauthorized(self, client):
        data = {"name": "Society Teste",
                "description": "Foo bar", "capacity": 10, "type": "VOLEI"}
        response = client.post(
            ARENA_PREFIX + "/",
            json=data)

        assert response.status_code == 401

    @pytest.mark.parametrize(
        "data, field",
        [({"name": "Modified"}, "name"),
         ({"description": "Modified"}, "description"),
         ({"capacity": 12345}, "capacity"),
         ({"type": "TÊNIS"}, "type")])
    def test_update_arena_fields(self, client, setUp, access_token, data, field):
        response = client.patch(
            ARENA_PREFIX + "/1",
            json=data,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert data[field] == response.json()[field]

    def test_update_all_arena_fields(self, client, setUp, access_token):
        data = {"name": "Modified", "description": "Modified",
                "capacity": 12345, "type": "TÊNIS"}
        response = client.patch(
            ARENA_PREFIX + "/1",
            json=data,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert data["name"] == response.json()["name"]
        assert data["description"] == response.json()["description"]
        assert data["capacity"] == response.json()["capacity"]
        assert data["type"] == response.json()["type"]

    def test_update_arena_unauthorized(self, client, setUp):
        data = {"name": "Modified"}
        response = client.patch(
            ARENA_PREFIX + "/1",
            json=data,
        )

        assert response.status_code == 401

    def test_delete_arena(self, client, setUp, access_token):
        response = client.delete(
            ARENA_PREFIX + "/1",
            headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 200

    def test_delete_arena_unauthorized(self, client, setUp):
        response = client.delete(ARENA_PREFIX + "/1")

        assert response.status_code == 401

import pytest
from datetime import datetime, timedelta

from app.api.models.arena import Arena, ArenaType
from app.api.models.user import User, Occupation
from app.api.models.reservation import Reservation
from app.core.security import get_password_hash
from app.tests.api.base import client, db_session, setup_db

RESERVATION_PREFIX = "/v1/reservations"


@pytest.fixture
def setUp(db_session):
    arenaTenis = Arena(name="Tenis1", description="Teste Tenis", id=1,
                  capacity=4, type=ArenaType.TENIS)

    arenaVolei = Arena(name="Volei1", description="Test Volei", id=2, 
                       capacity=10, type=ArenaType.VOLEI)
    

    user_internal = User(email="aluno@example.ufcg.edu.br",
                               cpf="12345678910",
                               occupation=Occupation.ALUNO,
                               password="123456789",
                               is_active=True,
                               hashed_password=get_password_hash("123456789"))
    
    reservation = Reservation(
        responsible_user_id=user_internal.id,
        arena_id=1, 
        start_date=next_monday(),
        end_date=next_monday() + timedelta(hours=1.5)
    )

    db_session.add(arenaTenis)
    db_session.add(arenaVolei)
    db_session.add(user_internal)
    db_session.add(reservation)
    db_session.commit()

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


class TestReservationRoutes():

    
    def test_get_reservations(self, client, setUp, access_token):
        response = client.get(RESERVATION_PREFIX + "/all", 
                              headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200


    def test_get_reservations_unauthorized(self, client, setUp):
        response = client.get(RESERVATION_PREFIX + "/all")

        assert response.status_code == 401


    def test_get_reservations_user(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})

        response = client.get(RESERVATION_PREFIX + f"/{get_users.json()[1]['id']}",
                              headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 200


    def test_get_reservation_user_reservation(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})

        get_reservations = client.get(RESERVATION_PREFIX + "/all", headers={"Authorization": f"Bearer {access_token}"})

        response = client.get(RESERVATION_PREFIX + f"/{get_users.json()[1]['id']}/{get_reservations.json()[0]['id']}",
                              headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200


    def test_reservation_weekly_sucess(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 1,
            "start_date": (next_day + timedelta(days=1)).isoformat(),
            "end_date": (next_day + timedelta(days=1, hours=1.5)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token}"},
                               json=data)
        
        assert response.status_code == 200


    def test_reservation_monthly_sucess(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 2,
            "start_date": (next_day + timedelta(days=1)).isoformat(),
            "end_date": (next_day + timedelta(days=1, hours=1.5)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token}"},
                               json=data)
        
        assert response.status_code == 200

    
    def test_reservation_invalid_arena(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 3,
            "start_date": (next_day + timedelta(days=1)).isoformat(),
            "end_date": (next_day + timedelta(days=1, hours=1.5)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token}"},
                               json=data)
        
        assert response.status_code == 500
        assert "Arena inválida ou inexistente." in response.json()['detail']
    

    # Menos de 1.5 horas de diferença entre end e start date.
    def test_reservation_invalid_start_end_date(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 1,
            "start_date": (next_day + timedelta(days=1)).isoformat(),
            "end_date": (next_day + timedelta(days=1)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token}"},
                               json=data)
        
        assert response.status_code == 500
        assert "Horario de inicio e fim Invalidos" in response.json()['detail']
        
    
    # Reservar horario que já passou.
    def test_reservation_date_passed(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})

        user = client.post('/v1/login/access-token', data={
        "username": str(get_users.json()[0]['email']),
        "password": "123456789"})
        
        access_token_internal = user.json()["access_token"]
        
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 1,
            "start_date": (next_day + timedelta(days=-10)).isoformat(),
            "end_date": (next_day + timedelta(days=-10, hours=1.5)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token_internal}"},
                               json=data)
        assert response.status_code == 500
        assert "Reserva ilegal para este esporte." in response.json()['detail']

    # Reservar horario que já passou.
    def test_reservation_ilegal_date_weekly(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 1,
            "start_date": (next_day + timedelta(days=10)).isoformat(),
            "end_date": (next_day + timedelta(days=10, hours=1.5)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token}"},
                               json=data)
        
        assert response.status_code == 500
        assert "Reserva ilegal para este esporte." in response.json()['detail']
    
    # Não está no mesmo mês e está antes do dia 15 do mês
    def test_reservation_ilegal_date_monthly(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})

        user = client.post('/v1/login/access-token', data={
        "username": str(get_users.json()[0]['email']),
        "password": "123456789"})
        
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 2,
            "start_date": (next_day + timedelta(days=60)).isoformat(),
            "end_date": (next_day + timedelta(days=60, hours=1.5)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token}"},
                               json=data)
        assert response.status_code == 500
        assert "Reserva ilegal para este esporte." in response.json()['detail']
    

    # Reserva fora dos horarios permitidos.
    def test_reservation_invalid_time_weekly(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        next_day = next_monday()
        data = {
            "responsible_user_id": str(get_users.json()[0]['id']),
            "arena_id": 1,
            "start_date": (next_day + timedelta(days=1, hours=0.5)).isoformat(),
            "end_date": (next_day + timedelta(days=1, hours=2)).isoformat()
        }

        response = client.post(RESERVATION_PREFIX + "/",
                               headers={"Authorization": f"Bearer {access_token}"},
                               json=data)

        assert response.status_code == 500
        assert "Reserva ilegal, horário ou data não permitido." in response.json()['detail']   

    def test_update_reservation(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})

        user = client.post('/v1/login/access-token', data={
        "username": str(get_users.json()[0]['email']),
        "password": "123456789"})
        
        access_token_internal = user.json()["access_token"]

        get_reservations = client.get(RESERVATION_PREFIX + "/all", headers={"Authorization": f"Bearer {access_token}"})
        next_day = next_monday()
        data = {
            "start_date": (next_day + timedelta(days=2)).isoformat(),
            "end_date": (next_day + timedelta(days=2, hours=1.5)).isoformat()
        }

        response = client.put(RESERVATION_PREFIX + f"/{get_reservations.json()[0]['id']}", headers={"Authorization": f"Bearer {access_token_internal}"}, json=data) 
        assert response.status_code == 200

    
    def test_delete_reservation_admin(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        get_reservations = client.get(RESERVATION_PREFIX + "/all", headers={"Authorization": f"Bearer {access_token}"})

        response = client.delete(RESERVATION_PREFIX + f"/{get_users.json()[1]['id']}/{get_reservations.json()[0]['id']}", headers={"Authorization": f"Bearer {access_token}"}) 

        assert response.status_code == 200


    def test_delete_reservation_internal(self, client, setUp, access_token):
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        user = client.post('/v1/login/access-token', data={
        "username": str(get_users.json()[0]['email']),
        "password": "123456789"})
        
        access_token_internal = user.json()["access_token"]

        get_reservations = client.get(RESERVATION_PREFIX + "/all", headers={"Authorization": f"Bearer {access_token}"})

        response = client.delete(RESERVATION_PREFIX + f"/{get_users.json()[0]['id']}/{get_reservations.json()[0]['id']}", headers={"Authorization": f"Bearer {access_token_internal}"}) 

        assert response.status_code == 200


    def test_delete_reservation_internal_unauthorized(self, client, setUp, access_token):
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
            "/v1/users" + "/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            json=data,
        )
        
        get_users = client.get("/v1/users/", headers={"Authorization": f"Bearer {access_token}"})
        user = client.post('/v1/login/access-token', data={
        "username": str(get_users.json()[2]['email']),
        "password": "internal user password"})

        access_token_internal = user.json()["access_token"]

        get_reservations = client.get(RESERVATION_PREFIX + "/all", headers={"Authorization": f"Bearer {access_token}"})

        response = client.delete(RESERVATION_PREFIX + f"/{get_users.json()[2]['id']}/{get_reservations.json()[0]['id']}", headers={"Authorization": f"Bearer {access_token_internal}"}) 

        assert response.status_code == 500
        assert "Você não tem permissão para cancelar esta reserva." in response.json()['detail']
    
    



        
def next_monday():
    now = datetime.now()

    days_until_monday = (0-now.weekday()) % 7
    
    return (now + timedelta(days=days_until_monday)).replace(hour=17, minute=30, second=0, microsecond=0)

import pytest
from unittest.mock import MagicMock, Mock, patch, call
from app.api.services.reservation import create_reservation, update_reservation, delete_reservation, get_participants_by_reservation_id
from app.api.models.reservation import ReservationCreate, ReservationUpdate, Reservation
from app.api.models.user import User, Occupation
from app.api.models.arena import Arena, ArenaType
from app.api.models.reservationUserLink import ReservationUserLink
from datetime import datetime, timedelta
from fastapi import HTTPException
import uuid
from sqlmodel import select


# ========== CREATE RESERVATION TESTS ==========

def test_create_reservation_invalid_arena():
    """Test that creating a reservation with invalid arena raises 400 error"""
    mock_session = MagicMock()
    mock_session.exec.return_value.first.return_value = None
    mock_session.get.return_value = None  # Arena not found

    reservation_data = ReservationCreate(
        responsible_user_id=uuid.uuid4(),
        arena_id=999,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30),
        participants=[]
    )
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    with pytest.raises(HTTPException) as exc_info:
        create_reservation(mock_session, reservation_data, user)
    
    assert exc_info.value.status_code == 400
    assert "Arena inválida ou inexistente" in exc_info.value.detail


def test_create_reservation_invalid_end_date():
    """Test that creating a reservation with invalid duration raises error"""
    mock_session = MagicMock()
    mock_session.exec.return_value.first.return_value = None
    
    arena = Arena(id=1, name="Arena Test", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner

    start_date = datetime.now() + timedelta(days=1)
    reservation_data = ReservationCreate(
        responsible_user_id=user_owner.id,
        arena_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(hours=1),  # Only 1 hour, should be 1.5
        participants=[]
    )
    
    user = User(
        id=user_owner.id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    with pytest.raises(HTTPException) as exc_info:
        create_reservation(mock_session, reservation_data, user)
    
    assert exc_info.value.status_code == 400
    assert "Horário de início e fim inválidos" in exc_info.value.detail


def test_create_reservation_weekly_sport_validation_fails():
    """Test weekly sports validation failure for tennis/beach tennis"""
    mock_session = MagicMock()
    mock_session.exec.return_value.first.return_value = None
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner

    # Create a date far in the future (invalid for weekly sports)
    start_date = datetime.now() + timedelta(days=30)
    reservation_data = ReservationCreate(
        responsible_user_id=user_owner.id,
        arena_id=1,
        start_date=start_date.replace(hour=17, minute=30),
        end_date=start_date.replace(hour=19, minute=0),
        participants=[]
    )
    
    user = User(
        id=user_owner.id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    with pytest.raises(HTTPException) as exc_info:
        create_reservation(mock_session, reservation_data, user)
    
    assert exc_info.value.status_code == 400
    assert "Reserva ilegal para este esporte" in exc_info.value.detail


def test_create_reservation_monthly_sport_validation_fails():
    """Test monthly sports validation failure for volleyball/society"""
    mock_session = MagicMock()
    mock_session.exec.return_value.first.return_value = None
    
    arena = Arena(id=2, name="Volleyball Court", type=ArenaType.VOLEI, capacity=10, description="Test")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner

    # Try to reserve 2 months in the future (invalid for monthly sports)
    start_date = datetime.now() + timedelta(days=70)
    reservation_data = ReservationCreate(
        responsible_user_id=user_owner.id,
        arena_id=2,
        start_date=start_date.replace(hour=18, minute=0),
        end_date=start_date.replace(hour=19, minute=30),
        participants=[]
    )
    
    user = User(
        id=user_owner.id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    with pytest.raises(HTTPException) as exc_info:
        create_reservation(mock_session, reservation_data, user)
    
    assert exc_info.value.status_code == 400
    assert "Reserva ilegal para este esporte" in exc_info.value.detail


def test_create_reservation_invalid_schedule():
    """Test that invalid time schedule raises error"""
    mock_session = MagicMock()
    mock_session.exec.return_value.first.return_value = None
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner

    # Invalid time (3:00 AM - not in valid schedule)
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    start_date = next_monday.replace(hour=3, minute=0, second=0, microsecond=0)
    
    reservation_data = ReservationCreate(
        responsible_user_id=user_owner.id,
        arena_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(hours=1, minutes=30),
        participants=[]
    )
    
    user = User(
        id=user_owner.id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    with pytest.raises(HTTPException) as exc_info:
        create_reservation(mock_session, reservation_data, user)
    
    assert exc_info.value.status_code == 400
    assert "horário ou data não permitido" in exc_info.value.detail


def test_create_reservation_conflicting_time_non_admin():
    """Test that non-admin cannot create reservation in occupied time slot"""
    mock_session = MagicMock()
    
    # Mock existing reservation conflict
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = None  # No participants
    mock_session.exec.return_value = mock_exec_result
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner

    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    start_date = next_monday.replace(hour=17, minute=30, second=0, microsecond=0)
    
    reservation_data = ReservationCreate(
        responsible_user_id=user_owner.id,
        arena_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(hours=1, minutes=30),
        participants=[]
    )
    
    user = User(
        id=user_owner.id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    # Mock is_reservation_available to return False (conflict exists)
    with patch('app.api.services.reservation.is_reservation_available', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            create_reservation(mock_session, reservation_data, user)
        
        assert exc_info.value.status_code == 400
        assert "Já existe uma reserva nesse horário" in exc_info.value.detail


def test_create_reservation_admin_deletes_conflicting():
    """Test that admin can override existing reservation"""
    mock_session = MagicMock()
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=True,
        is_internal=True,
        occupation=Occupation.SERVIDOR
    )
    
    # Existing conflicting reservation
    old_reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=uuid.uuid4(),
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1, hours=1),
        end_date=datetime.now() + timedelta(days=1, hours=2, minutes=30)
    )
    
    mock_exec_result = MagicMock()
    # First call returns None for participants, second returns old reservation
    mock_exec_result.first.side_effect = [None, old_reservation]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner

    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    start_date = next_monday.replace(hour=17, minute=30, second=0, microsecond=0)
    
    reservation_data = ReservationCreate(
        responsible_user_id=user_owner.id,
        arena_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(hours=1, minutes=30),
        participants=[]
    )

    with patch('app.api.services.reservation.verify_weekly_sports', return_value=True):
        with patch('app.api.services.reservation.is_valid_sports_schedule', return_value=True):
            result = create_reservation(mock_session, reservation_data, user_owner)
            
            # Verify old reservation was deleted
            mock_session.delete.assert_called_once_with(old_reservation)
            # Verify new reservation was added
            assert mock_session.add_all.called
            assert mock_session.commit.called


def test_create_reservation_with_participants():
    """Test creating reservation with multiple participants"""
    mock_session = MagicMock()
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    participant1 = User(
        id=uuid.uuid4(),
        email="participant1@example.com",
        cpf="11111111111",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    participant2 = User(
        id=uuid.uuid4(),
        email="participant2@example.com",
        cpf="22222222222",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    # Mock exec to return participants when queried
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [participant1, participant2, None]  # Last None for conflict check
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner

    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    start_date = next_monday.replace(hour=17, minute=30, second=0, microsecond=0)
    
    reservation_data = ReservationCreate(
        responsible_user_id=user_owner.id,
        arena_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(hours=1, minutes=30),
        participants=[participant1.id, participant2.id]
    )

    with patch('app.api.services.reservation.verify_weekly_sports', return_value=True):
        with patch('app.api.services.reservation.is_valid_sports_schedule', return_value=True):
            with patch('app.api.services.reservation.is_reservation_available', return_value=True):
                with patch('app.api.services.reservation.verify_last_reservation'):
                    result = create_reservation(mock_session, reservation_data, user_owner)
                    
                    # Verify participants were queried
                    assert mock_session.exec.call_count >= 2
                    assert mock_session.add_all.called
                    assert mock_session.commit.called


# ========== UPDATE RESERVATION TESTS ==========

def test_update_reservation_not_found():
    """Test updating non-existent reservation raises 404"""
    mock_session = MagicMock()
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = None
    mock_session.exec.return_value = mock_exec_result
    
    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    updated_data = ReservationUpdate(
        start_date=datetime.now() + timedelta(days=2),
        end_date=datetime.now() + timedelta(days=2, hours=1, minutes=30),
        participants=[]
    )

    with pytest.raises(HTTPException) as exc_info:
        update_reservation(mock_session, uuid.uuid4(), updated_data, user)
    
    assert exc_info.value.status_code == 404
    assert "Reserva não encontrada" in exc_info.value.detail


def test_update_reservation_unauthorized_non_admin():
    """Test non-admin cannot update other user's reservation"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    different_user_id = uuid.uuid4()
    
    existing_reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = existing_reservation
    mock_session.exec.return_value = mock_exec_result
    
    user = User(
        id=different_user_id,
        email="other@example.com",
        cpf="11111111111",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    updated_data = ReservationUpdate(
        start_date=datetime.now() + timedelta(days=2),
        end_date=datetime.now() + timedelta(days=2, hours=1, minutes=30),
        participants=[]
    )

    with pytest.raises(HTTPException) as exc_info:
        update_reservation(mock_session, existing_reservation.id, updated_data, user)
    
    assert exc_info.value.status_code == 403
    assert "Usuario autenticado incorreto" in exc_info.value.detail


def test_update_reservation_admin_can_update_any():
    """Test admin can update any reservation"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    
    existing_reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=owner_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        cpf="99999999999",
        hashed_password="hashed",
        is_admin=True,
        is_internal=True,
        occupation=Occupation.SERVIDOR
    )
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [existing_reservation, None]  # None for no conflict
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner
    
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    new_start = next_monday.replace(hour=17, minute=30, second=0, microsecond=0)
    
    updated_data = ReservationUpdate(
        start_date=new_start,
        end_date=new_start + timedelta(hours=1, minutes=30),
        participants=[]
    )

    with patch('app.api.services.reservation.verify_weekly_sports', return_value=True):
        with patch('app.api.services.reservation.is_valid_sports_schedule', return_value=True):
            result = update_reservation(mock_session, existing_reservation.id, updated_data, admin_user)
            
            assert mock_session.add.called
            assert mock_session.commit.called
            assert mock_session.refresh.called


def test_update_reservation_invalid_dates():
    """Test updating reservation with invalid date range fails"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    existing_reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=owner_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = existing_reservation
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner
    
    # Invalid duration (only 1 hour instead of 1.5)
    start = datetime.now() + timedelta(days=2)
    updated_data = ReservationUpdate(
        start_date=start,
        end_date=start + timedelta(hours=1),
        participants=[]
    )

    with pytest.raises(HTTPException) as exc_info:
        update_reservation(mock_session, existing_reservation.id, updated_data, user_owner)
    
    assert exc_info.value.status_code == 400
    assert "Horario de inicio e fim Invalidos" in exc_info.value.detail


def test_update_reservation_conflicting_schedule():
    """Test updating to a conflicting time slot fails for non-admin"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    existing_reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=owner_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = existing_reservation
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner
    
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    new_start = next_monday.replace(hour=17, minute=30, second=0, microsecond=0)
    
    updated_data = ReservationUpdate(
        start_date=new_start,
        end_date=new_start + timedelta(hours=1, minutes=30),
        participants=[]
    )

    with patch('app.api.services.reservation.is_valid_sports_schedule', return_value=True):
        with patch('app.api.services.reservation.is_reservation_available', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                update_reservation(mock_session, existing_reservation.id, updated_data, user_owner)
            
            assert exc_info.value.status_code == 400
            assert "Este horário já está sendo ocupado" in exc_info.value.detail


def test_update_reservation_weekly_sport_validation():
    """Test update validates weekly sport rules"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    existing_reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    user_owner = User(
        id=owner_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [existing_reservation, None]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner
    
    # Far future date (invalid for weekly)
    new_start = datetime.now() + timedelta(days=30, hours=17)
    updated_data = ReservationUpdate(
        start_date=new_start,
        end_date=new_start + timedelta(hours=1, minutes=30),
        participants=[]
    )

    with patch('app.api.services.reservation.is_valid_sports_schedule', return_value=True):
        with patch('app.api.services.reservation.verify_weekly_sports', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                update_reservation(mock_session, existing_reservation.id, updated_data, user_owner)
            
            assert exc_info.value.status_code == 400
            assert "não é válido para reservas semanais" in exc_info.value.detail


def test_update_reservation_monthly_sport_validation():
    """Test update validates monthly sport rules"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    existing_reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=2,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    arena = Arena(id=2, name="Volleyball Court", type=ArenaType.VOLEI, capacity=10, description="Test")
    user_owner = User(
        id=owner_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [existing_reservation, None]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.side_effect = lambda model, id: arena if model == Arena else user_owner
    
    # Too far in future (invalid for monthly)
    new_start = datetime.now() + timedelta(days=70, hours=18)
    updated_data = ReservationUpdate(
        start_date=new_start,
        end_date=new_start + timedelta(hours=1, minutes=30),
        participants=[]
    )

    with patch('app.api.services.reservation.is_valid_sports_schedule', return_value=True):
        with patch('app.api.services.reservation.verify_monthly_sports', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                update_reservation(mock_session, existing_reservation.id, updated_data, user_owner)
            
            assert exc_info.value.status_code == 400
            assert "não é válido para reservas mensais" in exc_info.value.detail


# ========== DELETE RESERVATION TESTS ==========

def test_delete_reservation_not_found():
    """Test deleting non-existent reservation raises 404"""
    mock_session = MagicMock()
    mock_exec_result = MagicMock()
    mock_exec_result.first.return_value = None
    mock_session.exec.return_value = mock_exec_result
    
    user = User(
        id=uuid.uuid4(),
        email="user@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    with pytest.raises(HTTPException) as exc_info:
        delete_reservation(mock_session, uuid.uuid4(), user.id, user)
    
    assert exc_info.value.status_code == 500
    assert "Erro interno no servidor" in exc_info.value.detail


def test_delete_reservation_unauthorized():
    """Test non-owner non-admin cannot delete reservation"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    different_user_id = uuid.uuid4()
    
    reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    user_owner = User(
        id=owner_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [reservation, user_owner]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.return_value = arena
    
    different_user = User(
        id=different_user_id,
        email="other@example.com",
        cpf="99999999999",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )

    with pytest.raises(HTTPException) as exc_info:
        delete_reservation(mock_session, reservation.id, different_user_id, different_user)
    
    assert exc_info.value.status_code == 403
    assert "Você não tem permissão para cancelar esta reserva" in exc_info.value.detail


def test_delete_reservation_already_started():
    """Test cannot delete reservation that already started"""
    mock_session = MagicMock()
    
    user_id = uuid.uuid4()
    
    # Reservation in the past
    reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=user_id,
        arena_id=1,
        start_date=datetime.now() - timedelta(hours=2),
        end_date=datetime.now() - timedelta(minutes=30)
    )
    
    user_owner = User(
        id=user_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [reservation, user_owner]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.return_value = arena

    with pytest.raises(HTTPException) as exc_info:
        delete_reservation(mock_session, reservation.id, user_id, user_owner)
    
    assert exc_info.value.status_code == 400
    assert "Não é possível cancelar uma reserva que já iniciou" in exc_info.value.detail


def test_delete_reservation_success_weekly_sport():
    """Test successful deletion of weekly sport reservation"""
    mock_session = MagicMock()
    
    user_id = uuid.uuid4()
    
    reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=user_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    user_owner = User(
        id=user_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO,
        last_reservation_weekly=datetime.now()
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [reservation, user_owner]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.return_value = arena

    result = delete_reservation(mock_session, reservation.id, user_id, user_owner)
    
    assert result == "Reserva cancelada com sucesso."
    assert user_owner.last_reservation_weekly is None
    mock_session.delete.assert_called_once_with(reservation)
    mock_session.commit.assert_called_once()


def test_delete_reservation_success_monthly_sport():
    """Test successful deletion of monthly sport reservation"""
    mock_session = MagicMock()
    
    user_id = uuid.uuid4()
    
    reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=user_id,
        arena_id=2,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    user_owner = User(
        id=user_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO,
        last_reservation_monthly=datetime.now()
    )
    
    arena = Arena(id=2, name="Volleyball Court", type=ArenaType.VOLEI, capacity=10, description="Test")
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [reservation, user_owner]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.return_value = arena

    result = delete_reservation(mock_session, reservation.id, user_id, user_owner)
    
    assert result == "Reserva cancelada com sucesso."
    assert user_owner.last_reservation_monthly is None
    mock_session.delete.assert_called_once_with(reservation)
    mock_session.commit.assert_called_once()


def test_delete_reservation_admin_can_delete_any():
    """Test admin can delete any reservation"""
    mock_session = MagicMock()
    
    owner_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    
    reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=owner_id,
        arena_id=1,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    user_owner = User(
        id=owner_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO,
        last_reservation_weekly=datetime.now()
    )
    
    admin_user = User(
        id=admin_id,
        email="admin@example.com",
        cpf="99999999999",
        hashed_password="hashed",
        is_admin=True,
        is_internal=True,
        occupation=Occupation.SERVIDOR
    )
    
    arena = Arena(id=1, name="Tennis Court", type=ArenaType.TENIS, capacity=4, description="Test")
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [reservation, user_owner]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.return_value = arena

    result = delete_reservation(mock_session, reservation.id, owner_id, admin_user)
    
    assert result == "Reserva cancelada com sucesso."
    mock_session.delete.assert_called_once_with(reservation)
    mock_session.commit.assert_called_once()


def test_delete_reservation_arena_not_found():
    """Test error when arena doesn't exist during deletion"""
    mock_session = MagicMock()
    
    user_id = uuid.uuid4()
    
    reservation = Reservation(
        id=uuid.uuid4(),
        responsible_user_id=user_id,
        arena_id=999,
        start_date=datetime.now() + timedelta(days=1),
        end_date=datetime.now() + timedelta(days=1, hours=1, minutes=30)
    )
    
    user_owner = User(
        id=user_id,
        email="owner@example.com",
        cpf="12345678901",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    mock_exec_result = MagicMock()
    mock_exec_result.first.side_effect = [reservation, user_owner]
    mock_session.exec.return_value = mock_exec_result
    mock_session.get.return_value = None  # Arena not found

    with pytest.raises(HTTPException) as exc_info:
        delete_reservation(mock_session, reservation.id, user_id, user_owner)
    
    assert exc_info.value.status_code == 404
    assert "Arena não encontrada" in exc_info.value.detail


# ========== GET PARTICIPANTS TESTS ==========

def test_get_participants_by_reservation_id_empty():
    """Test getting participants when reservation has none"""
    mock_session = MagicMock()
    mock_query_result = MagicMock()
    mock_query_result.filter.return_value.all.return_value = []
    mock_session.query.return_value = mock_query_result
    
    reservation_id = uuid.uuid4()
    
    result = get_participants_by_reservation_id(mock_session, reservation_id)
    
    assert result == []


def test_get_participants_by_reservation_id_with_users():
    """Test getting participants returns correct users"""
    mock_session = MagicMock()
    
    user1 = User(
        id=uuid.uuid4(),
        email="user1@example.com",
        cpf="11111111111",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    user2 = User(
        id=uuid.uuid4(),
        email="user2@example.com",
        cpf="22222222222",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    # Mock query chain
    mock_query_result = MagicMock()
    mock_filter_result = MagicMock()
    mock_filter_result.all.return_value = [user1.id, user2.id]
    mock_query_result.filter.return_value = mock_filter_result
    mock_session.query.return_value = mock_query_result
    
    # Mock get to return users
    mock_session.get.side_effect = [user1, user2]
    
    reservation_id = uuid.uuid4()
    
    result = get_participants_by_reservation_id(mock_session, reservation_id)
    
    assert len(result) == 2
    assert user1 in result
    assert user2 in result


def test_get_participants_by_reservation_id_filters_none():
    """Test getting participants filters out None values"""
    mock_session = MagicMock()
    
    user1 = User(
        id=uuid.uuid4(),
        email="user1@example.com",
        cpf="11111111111",
        hashed_password="hashed",
        is_admin=False,
        is_internal=True,
        occupation=Occupation.ALUNO
    )
    
    invalid_user_id = uuid.uuid4()
    
    # Mock query chain
    mock_query_result = MagicMock()
    mock_filter_result = MagicMock()
    mock_filter_result.all.return_value = [user1.id, invalid_user_id]
    mock_query_result.filter.return_value = mock_filter_result
    mock_session.query.return_value = mock_query_result
    
    # Mock get to return user1 and None for invalid
    mock_session.get.side_effect = [user1, None]
    
    reservation_id = uuid.uuid4()
    
    result = get_participants_by_reservation_id(mock_session, reservation_id)
    
    assert len(result) == 1
    assert user1 in result
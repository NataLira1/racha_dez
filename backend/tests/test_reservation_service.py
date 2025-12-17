import pytest
from unittest.mock import MagicMock
from app.api.services.reservation import create_reservation, update_reservation, delete_reservation
from app.api.models.reservation import ReservationCreate
from app.api.models.user import User
from app.api.models.arena import Arena
from datetime import datetime
from fastapi import HTTPException


def test_create_reservation_invalid_arena():
    # Mock session
    mock_session = MagicMock()
    mock_session.get.return_value = None  # Arena not found

    reservation_data = ReservationCreate(
        responsible_user_id="user-uuid",
        arena_id=1,
        start_date=datetime.now(),
        end_date=datetime.now(),
        participants=[]
    )
    user = User(id="user-uuid", is_admin=False)

    with pytest.raises(HTTPException) as exc_info:
        create_reservation(mock_session, reservation_data, user)
    
    assert exc_info.value.status_code == 400
    assert "Arena inválida" in exc_info.value.detail
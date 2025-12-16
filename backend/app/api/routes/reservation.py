import datetime
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.models.user import User
from sqlalchemy.orm import Session
from app.api.deps import CurrentUser, SessionDep, get_db, get_current_user
from app.api.models.reservation import Reservation, ReservationDates, ReservationUpdate, ReservationResponse
from app.api.services.reservation import create_reservation, delete_reservation, get_participants_by_reservation_id, update_reservation
from app.api.models.reservation import ReservationCreate
from app.core.db import get_session
from app.api.utils.utils import is_reservation_available

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.post("/", response_model=ReservationResponse)
def create_reservation_route(
    reservation_data: ReservationCreate,
    db: SessionDep,
    current_user: User = Depends(get_current_user)
    ):
    try:
        reservation = create_reservation(db, reservation_data, current_user)
        participants = get_participants_by_reservation_id(db,reservation.id)
        reservation_respose = ReservationResponse(
                id = reservation.id,
                responsible_user_id = reservation.responsible_user_id,
                arena_id = reservation.arena_id,
                start_date = reservation.start_date,
                end_date = reservation.end_date,
                participants = participants,
        )
        return reservation_respose
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar reserva: {str(e)}")

@router.put("/{reservation_id}", response_model=ReservationResponse)
def update_reservation_route(reservation_id: uuid.UUID, updated_data: ReservationUpdate, db: SessionDep, user: CurrentUser):
    try:
        
        reservation = update_reservation(db, reservation_id, updated_data, user)
        participants = get_participants_by_reservation_id(db,reservation_id)
        reservation_respose = ReservationResponse(
                id = reservation.id,
                responsible_user_id = reservation.responsible_user_id,
                arena_id = reservation.arena_id,
                start_date = reservation.start_date,
                end_date = reservation.end_date,
                participants = participants,
        )
        
        return reservation_respose
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Erro ao editar a reserva: {str(e)}")
    

@router.delete("/{user_id}/{reservation_id}", response_model=str)
def cancel_reservation_route(
    reservation_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return delete_reservation(db=db, reservation_id=reservation_id, user_id=user_id, user=current_user)


@router.get("/all", response_model=List[ReservationResponse])
def list_all_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Somente administradores podem listar todas as reservas.")
    
    try:
        reservations = db.query(Reservation).all()
        response = []
        for r in reservations:
            participants = get_participants_by_reservation_id(db,r.id)
            reservation_respose = ReservationResponse(
                id = r.id,
                responsible_user_id = r.responsible_user_id,
                arena_id = r.arena_id,
                start_date = r.start_date,
                end_date = r.end_date,
                participants = participants,
            )
            response.append(reservation_respose)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar reservas: {str(e)}")
    
@router.get("/{user_id}", response_model=List[ReservationResponse])
def list_user_reservations(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Você só pode ver suas próprias reservas ou ser um administrador.")

    try:
        reservations = db.query(Reservation).filter(Reservation.responsible_user_id == user_id).all()
        response = []
        for r in reservations:
            participants = get_participants_by_reservation_id(db,r.id)
            reservation_respose = ReservationResponse(
                id = r.id,
                responsible_user_id = r.responsible_user_id,
                arena_id = r.arena_id,
                start_date = r.start_date,
                end_date = r.end_date,
                participants = participants,
            )
            response.append(reservation_respose)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar reservas do usuário: {str(e)}")
    

@router.get("/{user_id}/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    user_id: uuid.UUID,
    reservation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Você só pode ver suas próprias reservas ou ser um administrador.")
    
    try:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).all()
        participants = get_participants_by_reservation_id(db,reservation_id)
        reservation_response = ReservationResponse(
                id = reservation[0].id,
                responsible_user_id = reservation[0].responsible_user_id,
                arena_id = reservation[0].arena_id,
                start_date = reservation[0].start_date,
                end_date = reservation[0].end_date,
                participants = participants,
        )
        return reservation_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar a reserva: {str(e)}")
    
    
@router.post("/arena/{arena_id}", response_model=bool)
def verify_date_arena(
    arena_id: int,
    dates: ReservationDates,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    try:
        return is_reservation_available(
            session=session,
            arena_id=arena_id,
            start_date=dates.start_date,
            end_date=dates.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
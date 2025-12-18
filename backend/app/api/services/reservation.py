from datetime import datetime
from sqlmodel import Session, select
import uuid
from fastapi import Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.api.models.reservationUserLink import ReservationUserLink
from app.api.models.reservation import Reservation, ReservationCreate, ReservationUpdate
from app.api.models.user import User
from app.api.utils.utils import verify_last_reservation, verify_monthly_sports, verify_weekly_sports, is_valid_sports_schedule, is_reservation_available, verify_end_date
from app.api.models.arena import Arena
    
def create_reservation(session: SessionDep, reservation_data: ReservationCreate, user: User):
    
    # Buscar usuários participantes
    """
    Create a new reservation, persist it, and return the created Reservation.
    
    Builds the participant list from IDs in reservation_data, validates arena existence, date ranges, sport-specific scheduling rules, and overall schedule availability. For non-admin users, ensures the time slot is free and verifies the user's last reservation constraints; for admin users, removes any overlapping existing reservation for the same arena. Persists the reservation and refreshes related objects before returning.
    
    Parameters:
        session (SessionDep): Database session used for queries and persistence.
        reservation_data (ReservationCreate): Data required to create the reservation, including responsible_user_id, arena_id, start_date, end_date, and participant IDs.
        user (User): The authenticated user performing the operation (used to determine admin privileges).
    
    Returns:
        Reservation: The created and persisted Reservation instance.
    
    Raises:
        HTTPException: With status 400 for invalid arena, invalid start/end dates, illegal sport-specific schedule, or when the time slot is already taken; 400 when cancellation/validation rules fail; may also raise other HTTPException statuses for authorization or not-found conditions triggered by validations.
    """
    lista_de_usuarios = []
    for user_uuid in reservation_data.participants:
        usuario = session.exec(select(User).filter(User.id == user_uuid)).first()
        if usuario:
            lista_de_usuarios.append(usuario)
        
    # Criar a reserva
    reservation = Reservation(
        responsible_user_id=reservation_data.responsible_user_id,
        arena_id=reservation_data.arena_id,
        start_date=reservation_data.start_date,
        end_date=reservation_data.end_date,
        participants=lista_de_usuarios,
    )
    
    arena = session.get(Arena, reservation.arena_id)
    user_owner = session.get(User, reservation.responsible_user_id)
    
    
    
    if not arena:
        raise HTTPException(status_code=400, detail="Arena inválida ou inexistente.")
    
    if not verify_end_date(reservation.start_date, reservation.end_date):
        raise HTTPException(status_code=400, detail="Horário de início e fim inválidos.")
    
    if arena.type in ["BEACH_TENNIS", "TÊNIS"]:
        if not verify_weekly_sports(reservation, arena, user_owner):
            raise HTTPException(status_code=400, detail="Reserva ilegal para este esporte.")
    else:
        if not verify_monthly_sports(reservation, arena, user_owner):
            raise HTTPException(status_code=400, detail="Reserva ilegal para este esporte.")
    
    if not is_valid_sports_schedule(reservation, arena):
        raise HTTPException(status_code=400, detail="Reserva ilegal, horário ou data não permitido.")
    
    if not user.is_admin:
        if not is_reservation_available(session, reservation.arena_id, reservation.end_date, reservation.start_date):
            raise HTTPException(status_code=400, detail="Já existe uma reserva nesse horário.")
        verify_last_reservation(arena, user_owner, reservation.start_date)
        
            
    else:
        old_reservation = session.exec(select(Reservation).filter(Reservation.arena_id == reservation.arena_id, Reservation.start_date < reservation.end_date, Reservation.end_date > reservation.start_date)).first()
        if old_reservation is not None:
            session.delete(old_reservation)
            
    
    
    
    # Adicionar e persistir a reserva
    session.add_all([reservation, user])
    session.commit()
    session.refresh(reservation)
    session.refresh(user)
    
    return reservation

def update_reservation(session: Session, reservation_id: int, updated_data: ReservationUpdate, user: User):
    """
    Update an existing reservation's dates and participants, applying authorization and schedule validations.
    
    Parameters:
        reservation_id (int): ID of the reservation to update.
        updated_data (ReservationUpdate): Fields to update (start_date, end_date, participants).
        user (User): Authenticated user performing the update; admins may edit any reservation.
    
    Returns:
        Reservation: The updated reservation object.
    
    Raises:
        HTTPException 404: If the reservation does not exist ("Reserva não encontrada.").
        HTTPException 403: If the requester is not an admin and is not the reservation owner ("Usuario autenticado incorreto").
        HTTPException 400: If start/end dates are invalid ("Horario de inicio e fim Invalidos"), if the time slot is occupied for non-admin users ("Este horário já está sendo ocupado por outra reserva."), if the schedule is not allowed for the arena type ("Horário inválido para este tipo de arena."), or if the weekly/monthly sport-specific validation fails ("Este horário não é válido para reservas semanais." / "Este horário não é válido para reservas mensais.").
    """
    reservation = session.exec(select(Reservation).filter(Reservation.id == reservation_id)).first()

    # Modificação: Permitir que administradores editem reservas
    if not user.is_admin and reservation.responsible_user_id != user.id:
        raise HTTPException(status_code=403, detail="Usuario autenticado incorreto")

    lista_de_usuarios = []
    for uuid in updated_data.participants:
        usuario = session.exec(select(User).filter(User.id == uuid)).first()
        if usuario:
            lista_de_usuarios.append(usuario)

    reservation_update = {
        "start_date": updated_data.start_date,
        "end_date": updated_data.end_date,
        "participants": lista_de_usuarios,
    }

    arena = session.get(Arena, reservation.arena_id)
    user_owner = session.get(User, reservation.responsible_user_id)

    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")

    for key, value in reservation_update.items():
        if value:
            setattr(reservation, key, value)

    if not verify_end_date(reservation.start_date, reservation.end_date):
        raise HTTPException(status_code=400, detail="Horario de inicio e fim Invalidos")

    if not is_valid_sports_schedule(reservation, arena):
        raise HTTPException(status_code=400, detail="Horário inválido para este tipo de arena.")

    if not user.is_admin:
        if is_reservation_available(session, reservation.arena_id, reservation.end_date, reservation.start_date):
            raise HTTPException(status_code=400, detail="Este horário já está sendo ocupado por outra reserva.")
    else:
        old_reservation = session.exec(select(Reservation).filter(Reservation.arena_id == reservation.arena_id,
                                                            Reservation.start_date < reservation_update["end_date"],
                                                            Reservation.end_date > reservation_update["start_date"])).first()
        if old_reservation is not None:
            session.delete(old_reservation)

    if arena.type in ["BEACH_TENNIS", "TÊNIS"]:
        if not verify_weekly_sports(reservation, arena, user_owner):
            raise HTTPException(status_code=400, detail="Este horário não é válido para reservas semanais.")
    else:
        if not verify_monthly_sports(reservation, arena, user_owner):
            raise HTTPException(status_code=400, detail="Este horário não é válido para reservas mensais.")

    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    return reservation


def delete_reservation(db: Session, reservation_id: uuid.UUID, user_id: uuid.UUID, user: User) -> str:
    
    """
    Cancel a reservation, delete it from the database, and clear the owner's last-reservation tracker for the relevant schedule window.
    
    Parameters:
        reservation_id (uuid.UUID): Identifier of the reservation to cancel.
        user_id (uuid.UUID): Identifier of the reservation owner (responsible user).
        user (User): Authenticated user requesting the cancellation; used for authorization checks.
    
    Returns:
        str: Confirmation message "Reserva cancelada com sucesso." on successful cancellation.
    
    Raises:
        HTTPException: 404 if the reservation is not found ("Reserva não encontrada.").
        HTTPException: 403 if the requester is neither the reservation owner nor an admin ("Você não tem permissão para cancelar esta reserva.").
        HTTPException: 404 if the associated arena is not found ("Arena não encontrada.").
        HTTPException: 400 if the reservation has already started ("Não é possível cancelar uma reserva que já iniciou.").
        HTTPException: 500 for internal server errors with the original error text appended.
    """
    try:
        reservation = db.exec(select(Reservation).filter(Reservation.id == reservation_id)).first()
        user_owner = db.exec(select(User).filter(User.id == user_id)).first()
        arena_id = reservation.arena_id
        arena = db.get(Arena, arena_id)
        
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        if reservation.responsible_user_id != user_id and not user.is_admin:
            raise HTTPException(status_code=403, detail="Você não tem permissão para cancelar esta reserva.")
        if not arena:
            raise HTTPException(status_code=404, detail="Arena não encontrada.")
        
        if reservation.start_date <= datetime.now():
            raise HTTPException(status_code=400, detail="Não é possível cancelar uma reserva que já iniciou.")
        else:
            if arena.type in ["TÊNIS" , "BEACH_TENNIS"]:
                user_owner.last_reservation_weekly = None
            else:
                user_owner.last_reservation_monthly = None
                
        db.add(user)
        db.delete(reservation)
        db.commit() 
        db.refresh(user)

        return "Reserva cancelada com sucesso."

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor. Por favor, tente novamente. {str(e)}")
    

def get_participants_by_reservation_id(session: Session,reservation_id: uuid.UUID):
    participants = []
    
    users = session.query(ReservationUserLink.user_id).filter(ReservationUserLink.reservation_id == reservation_id).all()
    
    for value in users:
        user = session.get(User, value)
        if user:
            participants.append(user)
            
    return participants
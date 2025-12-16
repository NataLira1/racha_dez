from pydantic import BaseModel
from sqlmodel import Relationship, SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

from app.api.models.reservationUserLink import ReservationUserLink
from app.api.models.user import User, UserPublic

# Modelo Base
class ReservationBase(SQLModel):
    responsible_user_id: uuid.UUID = Field(default=None)
    arena_id: int | None = Field(default=None)
    start_date: datetime
    end_date: datetime
    made_on: datetime = Field(default_factory=datetime.utcnow)
    

# Modelo de Banco de Dados
class Reservation(ReservationBase, table=True):
    participants: list["User"] = Relationship(back_populates="reservations", link_model=ReservationUserLink)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

# Modelo para criação de reserva
class ReservationCreate(SQLModel):
    responsible_user_id: uuid.UUID
    arena_id: int 
    start_date: datetime
    end_date: datetime
    participants: list[uuid.UUID] = Field(default=[]) 

class ReservationUpdate(SQLModel):
    start_date: datetime
    end_date: datetime
    participants: list[uuid.UUID] = Field(default=[])
    
class ReservationResponse(SQLModel):
    id: uuid.UUID
    responsible_user_id: uuid.UUID
    arena_id: int 
    start_date: datetime
    end_date: datetime
    participants: list[User] = Field(default=[]) 
    
    
class ReservationDates(BaseModel):
    start_date: datetime
    end_date: datetime
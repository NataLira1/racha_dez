from datetime import datetime
from typing import List
import uuid
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from app.api.models.reservationUserLink import ReservationUserLink

class Occupation(str, Enum):
    ALUNO = "ALUNO"
    SERVIDOR = "SERVIDOR"
    PROFESSOR = "PROFESSOR"
    EXTERNO = "EXTERNO"

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    cpf: str = Field(unique=True, index=True, max_length=11)
    phone: str | None = Field(default=None, max_length=11)
    occupation: Occupation = Field(default=Occupation.ALUNO)
    is_active: bool = False
    is_admin: bool = False
    is_internal: bool = True
    full_name: str | None = Field(default=None, max_length=255)
    last_reservation_monthly: datetime | None = None
    last_reservation_weekly: datetime | None = None
    
# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    cpf: str = Field(max_length=11)
    phone: str | None = Field(default=None, max_length=11)
    occupation: Occupation = Field(default=Occupation.ALUNO)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(  # type: ignore
        default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    reservations: list["Reservation"] = Relationship(back_populates="participants",link_model=ReservationUserLink)
    


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

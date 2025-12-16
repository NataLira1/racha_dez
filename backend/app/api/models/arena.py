from typing import Optional
from enum import Enum

from sqlmodel import Field, SQLModel


class ArenaType(str, Enum):
    VOLEI = "VOLEI"
    BEACH_TENNIS = "BEACH_TENNIS"
    SOCIETY = "SOCIETY"
    TENIS = "TÊNIS"


class ArenaBase(SQLModel):
    name: str
    description: str
    capacity: int
    type: ArenaType


class Arena(ArenaBase, table=True):
    id: int = Field(default=None, primary_key=True)


class ArenasPublic(SQLModel):
    data: list[Arena]
    count: int


class ArenaUpdate(SQLModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    capacity: Optional[int] = Field(default=None)
    type: Optional[ArenaType] = Field(default=None)

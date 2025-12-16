import re
from typing import Any
import uuid
from fastapi import HTTPException
from pydantic import EmailStr
from sqlmodel import Session, select
from app.api.models.user import Occupation
from app.api.services.login import dispatch_confirmation_email

from app.core.security import get_password_hash
from app.api.models.user import User, UserCreate, UserUpdate


def validate_email(email: EmailStr) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.ufcg\.edu\.br$"
    return bool(re.match(pattern, email))


def create_user(*, session: Session, user_create: UserCreate) -> User:
    if user_create.is_internal and user_create.occupation == Occupation.EXTERNO:
        raise HTTPException(
            status_code=400, detail="Internal user cannot have the occupation 'EXTERNO'"
        )

    if user_create.is_internal and not validate_email(user_create.email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email: must have a domain of ufcg.edu.br.",
        )

    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    user = get_user_by_email(session=session, email=user_create.email)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="User not found.",
        )

    dispatch_confirmation_email(user)

    return db_obj

def read_users(session: Session, offset: int, limit: int):
    """
    Retrieve users.
    """
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users


def get_blocked_users(session: Session, offset: int, limit: int):
    """
    Retrieve blocked users.
    """
    users = session.exec(select(User).where(User.is_active == False)).all()
    return users


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def active_user(*, session: Session, db_user: User) -> Any:
    db_user.is_active = True
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def get_user_by_cpf(*, session: Session, cpf: str) -> User | None:
    statement = select(User).where(User.cpf == cpf)
    session_user = session.exec(statement).first()
    return session_user

def verify_user(*,session: Session, email: str):
    user = get_user_by_email(session=session, email=email)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo ou bloqueado")
    
    return user
    

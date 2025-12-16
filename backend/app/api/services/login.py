from sqlmodel import Session
from app.api.models.user import User
from sqlmodel import select
from app.core.security import verify_password
from fastapi import HTTPException
from app.api.utils.utils import send_email
from app.core.security import create_access_token
from app.core.config import settings
from datetime import timedelta


def get_user_by_id(session: Session, email: str):
    statement = select(User).where(User.email == email)
    db_user = session.exec(statement).first()
    return db_user


def get_all_users(session: Session):
    statement = select(User)
    return session.exec(statement).all()


def update_password(session: Session, id: str, new_password):
    statement = select(User).where(User.id == id)
    user = session.exec(statement).first()

    if user:
        user.hashed_password = new_password
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        raise HTTPException(status_code=404, detail=f"Usuário com o id {id} não encontrado")


def authenticate(session: Session, email: str, password: str):
    db_user = get_user_by_id(session, email)

    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def dispatch_confirmation_email(user: User):
    token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    try:
        link = f"{settings.FRONTEND_URL}/confirm-email/{token}"
        send_email(
            email_to=user.email,
            subject=f"{settings.PROJECT_NAME} - Confirme seu email",
            content=f"Confirme seu email clicando nesse link: {link}",
        )
    except Exception as e:
        raise e


def dispatch_reset_password_email(email: str, token: str):
    try:
        link = f"{settings.FRONTEND_URL}/redefinir-senha/{token}"
        send_email(
            email_to=email,
            subject=f"{settings.PROJECT_NAME} - Mude sua senha",
            content=f"Confirme sua mudança de senha clicando nesse link: {link}",
        )
    except Exception as e:
        raise e

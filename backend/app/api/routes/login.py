from app.api.deps import CurrentUser, SessionDep
import uuid
from app.api.models import token
from app.api.models.token import Token
from typing import Annotated, Any
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.core import security
from app.core.security import get_password_hash
from app.api.services import login as login_service
from app.api.models.user import UserPublic, NewPassword, User
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import jwt
from app.core.config import settings
from app.core.security import ALGORITHM


from app.api.utils.utils import (
    generate_password_reset_token,
    send_email,
    verify_password_reset_token,
)

from app.api.services import user as user_service

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = login_service.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(status_code=400, detail="Email ou senha incorretos.")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo. Por favor, verifique seu e-mail para confirmar o seu cadastro.")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> str:
    """
    Password Recovery
    """
    user = user_service.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Não existe um usuário com esse email no sistema.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    login_service.dispatch_reset_password_email(email=email, token=password_reset_token)
    return "Email de recuperação de senha enviado."


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> str:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido.")
    user = user_service.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Não existe um usuário com esse email no sistema.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo. Por favor, verifique seu e-mail para confirmar o seu cadastro.")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return "Senha atualizada com sucesso."

@router.get("/login/confirm-email/{token}", response_model=UserPublic)
def confirm_email(token: str, session: SessionDep):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expirado.")
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token inválido.")

    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user.is_active = True
    session.add(user)
    session.commit()

    return user

from datetime import datetime, timedelta, timezone, time

import uuid
from fastapi import HTTPException

from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
import jwt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core import security
from app.api.models.reservation import Reservation
from app.api.models.user import User
from app.core.config import settings
from app.api.models.arena import Arena
from app.api.models.reservation import Reservation


def send_email(*, email_to: str, subject: str, content: str):
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = email_to
    msg["Subject"] = subject

    msg.attach(MIMEText(content, "plain"))

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, email_to, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


def verify_weekly_sports(reservation: Reservation, arena: Arena, user: User) -> bool:
    start_date = reservation.start_date

    now = datetime.now()
    today = now.date()
    thursday_15h = today + timedelta(days=(3 - today.weekday() + 7) % 7)
    thursday_15h = datetime.combine(thursday_15h, datetime.min.time()) + timedelta(
        hours=15
    )

    if arena.type in ["BEACH_TENNIS", "TÊNIS"]:
        if user.is_internal:
            # Usuários internos podem reservar qualquer horário na semana que estão ou na próxima semana (depois de quinta-feira 15h)
            
            #Verifica se a data já passou
            if start_date.date() < today:
                return False
            #Verifica se está na mesma semana
            if start_date.date() >= today and start_date.isocalendar()[:2] == today.isocalendar()[:2]:
                return True
            if start_date.date() > today + timedelta(days=7) and now < thursday_15h:
                return False
        else:
            # Usuários externos só podem marcar no fim de semana (sábado e domingo) e dentro dos intervalos de 1h30min
            if start_date.weekday() in [5, 6]:  # Sábado (5) ou Domingo (6)
                valid_times = [
                    time(5, 30),
                    time(7, 0),
                    time(8, 30),
                    time(10, 0),
                    time(11, 30),
                    time(13, 0),
                    time(14, 30),
                    time(16, 0),
                    time(17, 30),
                ]
                if start_date.time() in valid_times and time(
                    5, 30
                ) <= start_date.time() < time(18, 0):
                    return True
            return False
    return True


def verify_monthly_sports(reservation: Reservation, arena: Arena, user: User) -> bool:
    start_date = reservation.start_date

    now = datetime.now()
    today = now.date()

    fifteenth_of_month = today.replace(day=15)

    if arena.type in ["VOLEI", "SOCIETY"]:
        if user.is_internal:
            # Usuários internos podem marcar rachas para o mês atual ou o próximo mês após o dia 15
            
            #Verifica se a data já passou
            if start_date.date() < today:
                return False
            if start_date.month == today.month:
                return True
            if start_date.month == today.month + 1 or (
                today.month == 12 and start_date.month == 1
            ):
                if now.date() >= fifteenth_of_month:
                    return True
            return False
        else:
            return False
          
        
    return True
    




def is_valid_sports_schedule(reservation: Reservation, arena: Arena) -> bool:
    start_time = reservation.start_date.time()
    start_weekday = reservation.start_date.weekday()

    valid_times_weekly = [
        time(5, 30), time(7, 0), time(8, 30), time(10, 0), time(11, 30),
        time(13, 0), time(14, 30), time(16, 0), time(17, 30), time(19, 00)
    ]
    valid_times_society = [time(18, 0), time(19, 30)]

    if arena.type in ["BEACH_TENNIS", "TÊNIS", "VOLEI"]:
        if start_weekday < 5:  # Dias úteis (segunda a sexta)
            if (
                time(5, 30) <= start_time < time(21, 0)
                and start_time in valid_times_weekly
            ):
                return True
        else:  # Finais de semana (sábado e domingo)
            if (
                time(5, 30) <= start_time < time(18, 0)
                and start_time in valid_times_weekly
            ):
                return True
        return False

    if arena.type == "SOCIETY":
        if (
            start_weekday in [2, 4] and start_time in valid_times_society
        ):  # Quarta ou sexta-feira
            return True
        return False

    return False


def is_reservation_available(session: Session, arena_id: int,end_date: datetime, start_date: datetime ) -> bool:
    
    

    existing_reservation = session.query(Reservation).filter(
        Reservation.arena_id == arena_id,  
        Reservation.start_date < end_date,
        Reservation.end_date > start_date
    ).first()

    return existing_reservation is None

def is_previous_week(date: datetime) -> bool:
    """
    Verifica se a data fornecida pertence a uma semana anterior à atual.

    Retorna:
    - True: Se a data estiver em uma semana anterior à semana atual.
    - False: Se a data estiver na semana atual ou no futuro.
    """

    if date is None:
        return True

    today = datetime.today()

    # Calcula o início da semana atual (segunda-feira da semana atual)
    start_of_week = today - timedelta(days=today.weekday())

    # Se a data for antes do início da semana atual, pertence a uma semana anterior
    return date < start_of_week


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_end_date(start_date: datetime, end_date: datetime):
    return end_date - start_date == timedelta(hours=1, minutes=30)


def verify_last_reservation(arena: Arena, user: User, start_date: datetime):
    if arena.type in ["VOLEI", "SOCIETY"]:
        if verify_last_reservation_monthly(user.last_reservation_monthly):
            user.last_reservation_monthly = start_date
    elif arena.type in ["BEACH_TENNIS", "TÊNIS"]:
        if verify_last_reservation_weekly(user.last_reservation_weekly, start_date):
            user.last_reservation_weekly = start_date


def verify_last_reservation_monthly(last_reservation: datetime):
    if last_reservation is None:
        return True

    today = datetime.now()
    if last_reservation.month == today.month and last_reservation.year == today.year:
        raise HTTPException(
            status_code=400,
            detail="O usuário ainda não está liberado para fazer outra reserva este mês.",
        )

    return True


def verify_last_reservation_weekly(
    last_reservation: datetime | None, start_date: datetime
) -> bool:
    if last_reservation is None:
        return True

    start_date = start_date.replace(tzinfo=None)
    last_reservation = last_reservation.replace(tzinfo=None)

    if start_date - last_reservation < timedelta(days=7):
        raise HTTPException(
            status_code=400,
            detail="O usuário ainda não está liberado para fazer outra reserva esta semana.",
        )

    return True

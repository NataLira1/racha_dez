import secrets


class Settings:
    PROJECT_NAME: str = "RACHADEZ"
    API_V1_STR: str = "/v1"
    # NOTE(winicius): We must need to get those variables from a `.env` file
    # so we do not need to pass the values hardcoded, but configure it before deploy.
    # This allow us to change between a development environment and production environment.
    # For example: in dev, the database runs on `localhost`, but in production we need to pass
    # the database container name, in this case it is just `db`.
    # For sake of simplicity, I'll leave just `db` and to run the API, you must use Make targets
    # so I've configure run target to build the API.
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    # 60 minutes * 24 hours * 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "rachadez10@gmail.com"
    SMTP_PASSWORD: str = "zvby bxlv ledq takm "
    EMAILS_FROM_NAME: str = "rachadez"
    EMAILS_FROM_EMAIL: str = "rachadez10@gmail.com"
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 1
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    URL_BASE: str = "http://localhost:8000/v1"
    FRONTEND_URL: str = "http://localhost:5173"

    CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:5173"]

    FIRST_SUPERUSER_FULL_NAME = "Administrador"
    FIRST_SUPERUSER_EMAIL: str = "admin@complexo.ufcg.edu.br"
    FIRST_SUPERUSER_PASSWORD: str = "adminadmin"
    FIRST_SUPERUSER_CPF: str = "00000000000"

    ARENAS: dict = {
        "Volei de areia 1": {"capacity": 10, "type": "VOLEI"},
        "Volei de areia 2": {"capacity": 10, "type": "VOLEI"},
        "Beach Tennis 1": {"capacity": 4, "type": "BEACH_TENNIS"},
        "Beach Tennis 2": {"capacity": 4, "type": "BEACH_TENNIS"},
        "Tenis": {"capacity": 4, "type": "TÊNIS"},
        "Society": {"capacity": 10, "type": "SOCIETY"},
    }


settings = Settings()

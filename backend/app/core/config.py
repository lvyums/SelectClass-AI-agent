from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "course_selection"
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 8
    mimo_api_key: str = Field("", env="MIMO_API_KEY")
    mimo_api_url: str = Field("https://api.mimo.example/v1/chat/completions", env="MIMO_API_URL")
    mimo_model: str = Field("mimo-1", env="MIMO_MODEL")
    backend_port: int = Field(4000, env="BACKEND_PORT")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"],
        env="CORS_ORIGINS",
    )

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"


settings = Settings()

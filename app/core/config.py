from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql://postgres:password@localhost:5432/slt_ebill"
    output_dir: Path = Path("./output")
    log_level: str = "INFO"

    # JWT / Auth
    jwt_secret: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60


settings = Settings()

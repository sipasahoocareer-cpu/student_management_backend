from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        case_sensitive=False,
        extra="ignore"   # allow new MongoDB env vars without validation errors
    )
    
    SECRET_KEY: str
    DEBUG: bool = False
    ALGORITHM: str
    
    @field_validator('DEBUG', mode='before')
    @classmethod
    def validate_debug(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)

settings = Settings()
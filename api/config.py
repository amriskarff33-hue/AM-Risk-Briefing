from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://amrisk:changeme@db:5432/amrisk"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    SENTRY_DSN: str = ""
    LLM_PROVIDER: str = "none"
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_IDS: str = ""
    WHATSAPP_PROVIDER: str = "none"
    TWILIO_SID: str = ""
    TWILIO_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""
    WHATSAPP_TO: str = ""
    GREENAPI_ID: str = ""
    GREENAPI_TOKEN: str = ""
    GREENAPI_GROUP_ID: str = ""
    EMAIL_MODE: str = "none"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = ""
    EMAIL_TO: str = ""
    RESEND_API_KEY: str = ""
    GPU_ENABLED: bool = False
    GPU_MODEL_PATH: str = "/app/models"
    MAX_BRIEF_DURATION: int = 120
    APPROVAL_REQUIRED: bool = True
    AUTO_PUBLISH_EMAIL: bool = False
    DAILY_CRON_HOUR: int = 6
    DAILY_CRON_MINUTE: int = 0
    DATA_DIR: str = "/app/data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

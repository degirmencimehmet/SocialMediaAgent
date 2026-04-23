from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_OWNER_CHAT_ID: str = ""

    META_ACCESS_TOKEN: str = ""
    INSTAGRAM_ACCOUNT_ID: str = ""

    SERPAPI_KEY: str = ""

    DEFAULT_TENANT_ID: str = "hotel_001"
    DATABASE_URL: str = "sqlite:///./social_media_agent.db"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

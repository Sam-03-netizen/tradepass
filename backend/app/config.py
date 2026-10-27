from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./tradepass_dev.db"
    secret_key: str = "CHANGE_ME_TO_A_RANDOM_SECRET_BEFORE_DEPLOYMENT"
    access_token_expire_minutes: int = 60
    storage_dir: str = "./storage"
    frontend_origin: str = "http://localhost:5173"
    max_upload_mb: int = 10
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

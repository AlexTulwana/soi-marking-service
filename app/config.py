from pydantic_settings import BaseSettings, SettingsConfigDict


# All settings live here, read from the .env file.
# Model name is a setting, so changing models needs no code change.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    service_api_key: str = ""  # Laravel must send this in X-API-Key
    unreadable_below: float = 30.0  # OCR/AI confidence under this = unreadable


settings = Settings()

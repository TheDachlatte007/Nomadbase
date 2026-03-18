from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "NomadBase"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api"
    SEED_ALPHA_DATA: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

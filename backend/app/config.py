from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "NomadBase"
    DEBUG: bool = False
    APP_ENV: str = "alpha"
    API_V1_PREFIX: str = "/api"
    SEED_ALPHA_DATA: bool = False
    CORS_ALLOW_ORIGINS: str = "*"
    TRUSTED_HOSTS: str = "*"
    ENABLE_GZIP: bool = True
    IMPORT_AUTO_QUEUE_ON_CITY_CREATE: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        items = [item.strip() for item in value.split(",") if item.strip()]
        return items or ["*"]

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return self._parse_csv(self.CORS_ALLOW_ORIGINS)

    @property
    def trusted_hosts_list(self) -> list[str]:
        return self._parse_csv(self.TRUSTED_HOSTS)


settings = Settings()

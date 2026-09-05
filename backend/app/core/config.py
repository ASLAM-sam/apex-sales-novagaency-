from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings using Pydantic Settings.
    Loaded from environment variables or .env file.
    """

    APP_NAME: str = "Apex Sales AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    MONGODB_URI: str = ""
    MONGODB_DATABASE: str = "apex_sales"
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 5000

    SQLITE_DATABASE_PATH: str = "./data/apex_sales.sqlite3"

    LLM_PROVIDER: str = "omniroute"
    OMNIROUTE_API_KEY: str = ""
    OMNIROUTE_BASE_URL: str = "http://localhost:20128/v1"
    OMNIROUTE_DEFAULT_MODEL: str = ""
    OMNIROUTE_MODEL: str = ""
    OMNIROUTE_TIMEOUT_SECONDS: int = 60
    OMNIROUTE_MAX_RETRIES: int = 2

    EMAIL_PROVIDER: str = ""
    EMAIL_API_KEY: str = ""
    EMAIL_FROM: str = ""

    WHATSAPP_PROVIDER: str = ""
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""

    FRONTEND_URL: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    @property
    def mongodb_uri(self) -> str:
        return self.MONGODB_URI

    @property
    def mongodb_database(self) -> str:
        return self.MONGODB_DATABASE

    @property
    def mongodb_server_selection_timeout_ms(self) -> int:
        return self.MONGODB_SERVER_SELECTION_TIMEOUT_MS

    @property
    def sqlite_database_path(self) -> str:
        return self.SQLITE_DATABASE_PATH

    @property
    def omniroute_base_url(self) -> str:
        return self.OMNIROUTE_BASE_URL

    @property
    def omniroute_api_key(self) -> str:
        return self.OMNIROUTE_API_KEY

    @property
    def omniroute_default_model(self) -> str:
        return self.OMNIROUTE_DEFAULT_MODEL or self.OMNIROUTE_MODEL

    @property
    def omniroute_timeout_seconds(self) -> int:
        return self.OMNIROUTE_TIMEOUT_SECONDS

    @property
    def omniroute_max_retries(self) -> int:
        return self.OMNIROUTE_MAX_RETRIES

    def is_omniroute_configured(self) -> bool:
        """
        Checks if OmniRoute LLM gateway configuration is valid and not using placeholders.
        """
        placeholders = {
            "YOUR_OMNIROUTE_API_KEY",
            "YOUR_REAL_OMNIROUTE_API_KEY",
            "YOUR_OMNIROUTE_BASE_URL",
            "YOUR_OMNIROUTE_MODEL",
            "YOUR_OMNIROUTE_DEFAULT_MODEL",
            "",
        }
        api_key = self.omniroute_api_key.strip()
        base_url = self.omniroute_base_url.strip()

        if not api_key or api_key in placeholders:
            return False
        if not base_url or base_url in placeholders:
            return False
        return True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


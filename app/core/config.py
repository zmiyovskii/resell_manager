from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "resell_manager"
    debug: bool = True
    database_url: str
    manager_bot_token: str = ""
    default_carrier_fee: float = 10
    secret_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
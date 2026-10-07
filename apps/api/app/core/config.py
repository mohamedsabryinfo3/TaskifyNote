from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = ""
    cors_origins_raw: str = "http://localhost:3000"
    personal_api_key: str = ""
    gemini_api_key: str = ""
    ai_model: str = "gemini-3.8-flash"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [
            item.strip()
            for item in self.cors_origins_raw.split(",")
            if item.strip()
        ]


settings = Settings()

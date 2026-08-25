from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./civicguide.db"
    session_secret: str = "dev-session-secret-change-me"
    admin_token: str = "dev-admin-token"
    cors_origins: str = "http://localhost:3000"
    weight_eligibility: float = 0.35
    weight_need: float = 0.25
    weight_location: float = 0.15
    weight_profile: float = 0.10
    weight_education_occupation: float = 0.10
    weight_usefulness: float = 0.05
    embedding_model: str = "all-MiniLM-L6-v2"
    use_transformers: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

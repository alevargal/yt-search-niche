from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    youtube_api_key: str
    anthropic_api_key: str

    # Models: claude-opus-4-6 | claude-sonnet-4-6 | claude-haiku-4-5-20251001
    discovery_model: str = "claude-sonnet-4-6"   # finds niches from trending data
    analysis_model: str = "claude-sonnet-4-6"  # deep analysis per niche (haiku недостаточно для детального анализа)


settings = Settings()

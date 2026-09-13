from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================
    # Gemini
    # =========================

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    # =========================
    # Groq
    # =========================

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # =========================
    # Ollama
    # =========================

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3"

    # =========================
    # Supabase
    # =========================

    supabase_url: str = "https://egukapnjuhzekjwuzmek.supabase.co"
    supabase_key: str = "sb_publishable_HxebXvpYYDwtxuo-rR7Omg_WQ1Dyvbd"

    # =========================
    # Frontend / CORS
    # =========================

    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
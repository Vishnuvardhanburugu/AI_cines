"""Application configuration from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Semantic AI Prompt Enhancer"
    debug: bool = False
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # LLM provider: gemini | grok | openai | anthropic | local | mock
    llm_provider: str = "gemini"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    xai_api_key: str = ""
    xai_model: str = "grok-2-latest"
    xai_base_url: str = "https://api.x.ai/v1"
    local_base_url: str = "http://localhost:11434/v1"
    local_model: str = "llama3.2"

    # Image generation: auto | pollinations | gemini | huggingface | mock
    image_provider: str = "auto"
    pollinations_base_url: str = "https://image.pollinations.ai"
    gemini_image_model: str = "gemini-2.5-flash-image"
    hf_api_token: str = ""
    hf_image_model: str = "black-forest-labs/FLUX.1-schnell"
    image_timeout_seconds: float = 90.0
    image_max_prompt_length: int = 1500

    max_prompt_length: int = 12000
    request_timeout_seconds: float = 60.0
    rate_limit: str = "30/minute"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

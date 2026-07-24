from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FinScope UK"
    data_dir: str = Field(default=str(PROJECT_ROOT / "data"), alias="DATA_DIR")
    config_dir: str = Field(default=str(PROJECT_ROOT / "config"), alias="CONFIG_DIR")
    docs_dir: str = Field(default=str(PROJECT_ROOT / "docs"), alias="DOCS_DIR")
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    advisor_llm_provider: str = Field(default="deterministic", alias="ADVISOR_LLM_PROVIDER")
    advisor_llm_api_key: str | None = Field(default=None, alias="ADVISOR_LLM_API_KEY")
    advisor_llm_model: str = Field(default="gpt-4.1-mini", alias="ADVISOR_LLM_MODEL")
    advisor_llm_base_url: str = Field(default="https://api.openai.com/v1", alias="ADVISOR_LLM_BASE_URL")
    advisor_llm_timeout_seconds: float = Field(default=30, alias="ADVISOR_LLM_TIMEOUT_SECONDS")
    advisor_llm_max_output_tokens: int = Field(default=900, alias="ADVISOR_LLM_MAX_OUTPUT_TOKENS")
    advisor_llm_temperature: float | None = Field(default=0.2, alias="ADVISOR_LLM_TEMPERATURE")
    advisor_retrieval_mode: str = Field(default="lexical", alias="ADVISOR_RETRIEVAL_MODE")
    advisor_embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="ADVISOR_EMBEDDING_MODEL")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    openf1_base_url: str = "https://api.openf1.org/v1"
    openf1_username: str = ""
    openf1_password: str = ""
    openf1_access_token: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_origin_regex: str = r"https://.*\.vercel\.app"
    deepseek_api_key: str = ""
    openai_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"
    tavily_api_key: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    commercial_facts_db: str = "data/commercial_facts.sqlite"
    dashboard_preload: bool = True
    jolpica_base_url: str = "https://api.jolpi.ca/ergast/f1"
    season_window_years: int = 10
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    steward_vision_model: str = "qwen/qwen2.5-vl-72b-instruct"
    steward_reason_model: str = "deepseek/deepseek-r1"
    chroma_persist_dir: str = "data/chroma_fia"
    steward_use_chroma: bool = True
    pinecone_api_key: str = ""
    pinecone_index: str = "fia-sporting-regulations"
    pinecone_namespace: str = "fia-sporting-2026"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    embedding_model: str = "openai/text-embedding-3-small"
    fia_pdfs_dir: str = "app/data/pdfs"

    @property
    def pinecone_key(self) -> str:
        raw = (self.pinecone_api_key or "").strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
            raw = raw[1:-1].strip()
        return raw

    @property
    def openrouter_key(self) -> str:
        raw = (self.openrouter_api_key or "").strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
            raw = raw[1:-1].strip()
        return raw

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def llm_api_key(self) -> str:
        raw = (self.deepseek_api_key or self.openai_api_key or "").strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
            raw = raw[1:-1].strip()
        return raw


settings = Settings()

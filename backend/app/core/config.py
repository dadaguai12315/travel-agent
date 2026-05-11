from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "Travel Advisor"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://travel:travel@localhost:5432/travel_advisor"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"
    llm_max_tool_rounds: int = 5

    # Tavily Search
    tavily_api_key: str = ""

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Session TTL (seconds)
    session_ttl_seconds: int = 3600

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()

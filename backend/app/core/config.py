from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/primero"

    # AWS
    aws_region: str = "ap-northeast-2"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket: str = ""

    # Auth (Cognito 또는 JWT 직접 발급)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7일

    # Google OAuth (id_token 검증용 — 프론트와 동일한 Client ID)
    google_client_id: str = ""

    # 브라우저 자동화 (Playwright)
    browser_headless: bool = True

    # Bedrock
    bedrock_model_id: str = "anthropic.claude-sonnet-4-20250514"

    # Anthropic (직접 호출)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_base_url: str = ""  # 게이트웨이/프록시 사용 시. 비우면 기본 endpoint.

    # OpenClaw
    openclaw_api_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

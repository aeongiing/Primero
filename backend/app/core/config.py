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

    # OpenClaw
    openclaw_api_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

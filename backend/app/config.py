from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fsae_plm"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-this-to-a-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: str = "./storage"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "fsae-plm"

    class Config:
        env_file = ".env"


settings = Settings()

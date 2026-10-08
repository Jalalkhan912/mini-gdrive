from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://drive:drive@localhost:5432/drive"
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_bucket: str = "drive-blobs"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    max_upload_bytes: int = 100 * 1024 * 1024

    model_config = {"env_prefix": "DRIVE_"}


settings = Settings()

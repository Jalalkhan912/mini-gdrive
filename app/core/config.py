from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://drive:drive@localhost:5432/drive"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "drive-blobs"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    model_config = {"env_prefix": "DRIVE_"}


settings = Settings()

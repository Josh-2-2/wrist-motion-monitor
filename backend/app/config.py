from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_imu: str = "imu.readings"

    model_config = {"env_file": ".env"}


settings = Settings()

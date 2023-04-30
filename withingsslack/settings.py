from pathlib import Path
from pydantic import AnyHttpUrl, BaseSettings, HttpUrl


class Settings(BaseSettings):
    database_path: Path = "/tmp/data/withingsslack.db"
    withings_base_url: str = "https://wbsapi.withings.net/"
    withings_oauth_scopes: list[str] = ["user.metrics", "user.activity"]
    withings_client_secret: str
    withings_client_id: str
    withings_callback_url: AnyHttpUrl
    slack_webhook_url: HttpUrl

    class Config:
        env_file = ".env"


settings = Settings()

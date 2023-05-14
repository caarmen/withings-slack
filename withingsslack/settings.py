from pathlib import Path
from pydantic import AnyHttpUrl, BaseSettings, HttpUrl


class Settings(BaseSettings):
    database_path: Path = "/tmp/data/withingsslack.db"
    server_url: AnyHttpUrl
    withings_base_url: str = "https://wbsapi.withings.net/"
    withings_oauth_scopes: list[str] = ["user.metrics", "user.activity"]
    withings_client_secret: str
    withings_client_id: str
    withings_callback_url: AnyHttpUrl
    fitbit_base_url: str = "https://api.fitbit.com/"
    fitbit_oauth_scopes: list[str] = ["sleep"]
    fitbit_client_id: str
    fitbit_client_secret: str
    fitbit_poll_interval_s: int = 3600
    slack_webhook_url: HttpUrl

    class Config:
        env_file = ".env"


settings = Settings()

import dataclasses
from pathlib import Path

from pydantic import AnyHttpUrl, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclasses.dataclass
class WithingsOAuthSettings:
    name = "withings"
    base_url: str
    oauth_scopes: list[str]
    callback_url: str
    redirect_uri: str


class Settings(BaseSettings):
    database_path: Path = "/tmp/data/slackhealthbot.db"
    server_url: AnyHttpUrl
    withings_base_url: str = "https://wbsapi.withings.net/"
    withings_oauth_scopes: list[str] = ["user.metrics", "user.activity"]
    withings_client_secret: str
    withings_client_id: str
    withings_callback_url: AnyHttpUrl
    fitbit_base_url: str = "https://api.fitbit.com/"
    fitbit_oauth_scopes: list[str] = ["sleep", "activity"]
    fitbit_client_id: str
    fitbit_client_secret: str
    fitbit_client_subscriber_verification_code: str
    fitbit_poll_interval_s: int = 3600
    fitbit_poll_enabled: bool = True
    fitbit_activity_type_ids: list[int] = [
        # See https://dev.fitbit.com/build/reference/web-api/activity/get-all-activity-types/
        # for the list of all supported activity types and their ids
        55001,  # Spinning
        # 90013,  # Walk
        # 90001,  # Bike
        # 1071,   # Outdoor Bike
    ]
    slack_webhook_url: HttpUrl
    model_config = SettingsConfigDict(env_file=".env")

    @property
    def withings_oauth_settings(self):
        return WithingsOAuthSettings(
            base_url=self.withings_base_url,
            oauth_scopes=self.withings_oauth_scopes,
            callback_url=self.withings_callback_url,
            redirect_uri=f"{self.withings_callback_url}withings-oauth-webhook/",
        )


settings = Settings()
withings_oauth_settings = settings.withings_oauth_settings

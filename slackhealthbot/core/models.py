import dataclasses
import datetime


@dataclasses.dataclass
class OAuthFields:
    oauth_userid: str
    oauth_access_token: str
    oauth_refresh_token: str
    oauth_expiration_date: datetime

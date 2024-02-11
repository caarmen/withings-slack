from slackhealthbot.remoteservices.slack import messageapi
from slackhealthbot.settings import settings


async def do(slack_alias: str, service: str):
    message = f"""
Oh no <@{slack_alias}>, looks like you were logged out of {service}! 😳.
You'll need to log in again to get your reports:
{settings.server_url}v1/{service}-authorization/{slack_alias}
"""
    await messageapi.post_message(message)

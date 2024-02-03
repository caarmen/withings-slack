import httpx

from slackhealthbot.settings import settings


async def do(slack_alias: str, service: str):
    message = f"""
Oh no <@{slack_alias}>, looks like you were logged out of {service}! 😳.
You'll need to log in again to get your reports:
{settings.server_url}v1/{service}-authorization/{slack_alias}
"""
    async with httpx.AsyncClient() as client:
        await client.post(
            url=str(settings.slack_webhook_url),
            json={
                "text": message,
            },
        )

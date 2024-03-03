from fastapi.templating import Jinja2Templates

from slackhealthbot.data.database.connection import SessionLocal, ctx_db


async def get_db():
    db = SessionLocal()
    try:
        # We need to access the db session without having access to
        # fastapi's dependency injection. This happens when our update_token()
        # authlib function is called.
        # Set the db in a ContextVar to allow accessing it outside a fastapi route.
        ctx_db.set(db)
        yield db
    finally:
        await db.close()
        ctx_db.set(None)


templates = Jinja2Templates(directory="templates")

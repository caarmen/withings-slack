from slackhealthbot.database.connection import SessionLocal, ctx_db


async def get_db():
    db = SessionLocal()
    try:
        # We need to access the db session without having access to
        # fastapi's dependency injection. This happens when our update_token()
        # authlib function is called.
        # Set the db in a ContextVar to allow accessing it outside of a fastapi route.
        ctx_db.set(db)
        yield db
    finally:
        await db.close()
        ctx_db.set(None)

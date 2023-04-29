from . import connection, models


def init():
    models.Base.metadata.create_all(bind=connection.engine)

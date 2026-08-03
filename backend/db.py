from backend.database import db


def get_connection():
    return db.connect()
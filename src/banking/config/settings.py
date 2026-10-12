import os
from typing import TypedDict

from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig(TypedDict):
    host: str
    port: int
    dbname: str
    user: str
    password: str


def get_db_config() -> DatabaseConfig:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "banking_system"),
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", ""),
    }

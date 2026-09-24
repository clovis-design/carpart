import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

database_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("MYSQL_USER", "carpart"),
    password=os.getenv("MYSQL_PASSWORD", "carpart_dev"),
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3307")),
    database=os.getenv("MYSQL_DATABASE", "carpart_clients"),
    query={"charset": "utf8mb4"},
)
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as session:
        yield session

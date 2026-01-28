from sqlmodel import SQLModel, create_engine, Session
from app.config import settings
from typing import Generator

engine = create_engine(settings.DATABASE_URL, echo=settings.LOG_LEVEL == "debug")


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

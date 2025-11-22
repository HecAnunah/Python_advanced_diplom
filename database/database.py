import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv("app.env")  # для локальной разработки


class Base(AsyncAttrs, DeclarativeBase):
    def _repr(self, **fields):
        fields_str = ", ".join(f"{k}={v!r}" for k, v in fields.items())
        return f"<{self.__class__.__name__} {fields_str}>"


DATABASE_URL = (
    f'postgresql+asyncpg://{os.environ.get("POSTGRES_USER")}:'  # <--- здесь
    f'{os.environ.get("POSTGRES_PASSWORD")}@{os.environ.get("DB_HOST")}'
    f':{os.environ.get("DB_PORT")}/{os.environ.get("POSTGRES_DB")}'  # <--- здесь
)

print(DATABASE_URL + "+++++++++++++++++++++++++++++++++++++++")
engine = create_async_engine(DATABASE_URL, echo=True, future=True)
session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session() as db:
        try:
            yield db
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise

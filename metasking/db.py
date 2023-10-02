import os
# from typing import AsyncGenerator
from typing import Generator

from sqlmodel import create_engine, Session
# from sqlmodel.ext.asyncio.session import (
#     AsyncEngine  # type: ignore
# )

# from sqlalchemy.orm import sessionmaker

# from metasking.asyncsessionfix import AsyncSession


DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

# engine = AsyncEngine(create_engine(
#     DATABASE_URL, echo=True, future=True,
#     connect_args={"check_same_thread": False}
# ))
engine = create_engine(
    DATABASE_URL, echo=True, future=True,
    # connect_args={"check_same_thread": False}
)


# async def use_session() -> AsyncGenerator[AsyncSession, None]:
#     async_session = sessionmaker(
#         engine, class_=AsyncSession, expire_on_commit=False
#     )
#     async with async_session() as session:
#         yield session


def use_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

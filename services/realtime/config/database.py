from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST")
DB_PORT = config("DB_PORT", default=5432)
DB_NAME = config("DB_NAME")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create Engine (The main engine for connection)
# echo=True will help print the SQL query during development (similar to Django debug log).
engine = create_async_engine(
    DATABASE_URL,
    echo=config("DEBUG", default=False, cast=bool),
    future=True,
)

# Create Session (The session for connection)
# Every time a Request comes in, we will retrieve a Session from here.
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create Base (The base for all models)
Base = declarative_base()


# Dependency Injection Function
# This function is called by FastAPI to pass a session to the View Function.
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

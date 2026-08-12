from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import config
from database.models import Base

engine = create_async_engine(config.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Jadvallarni (agar mavjud bo'lmasa) yaratadi. Production'da alembic migratsiyasi tavsiya etiladi."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

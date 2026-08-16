from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import config
from database.models import Base

engine = create_async_engine(config.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Jadvallarni (agar mavjud bo'lmasa) yaratadi. Production'da alembic migratsiyasi tavsiya etiladi."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Mavjud production bazalarda ham yangi guruh bog'lash ustuni
        # avtomatik qo'shiladi. create_all mavjud jadvalga yangi ustun qo'shmaydi.
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS linked_group_chat_id BIGINT"
        )
        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_users_linked_group_chat_id "
            "ON users(linked_group_chat_id)"
        )
        await conn.exec_driver_sql(
            """CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                site_login VARCHAR(64) NOT NULL,
                message TEXT NOT NULL,
                is_sent BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )"""
        )
        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_notifications_pending "
            "ON notifications(is_sent, created_at)"
        )

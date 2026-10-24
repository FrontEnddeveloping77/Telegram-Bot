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
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS pricing_model VARCHAR(32)"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS product_count INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS max_products INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS max_groups INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tariff_price INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_reminder_at TIMESTAMPTZ"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS deletion_warning_count INTEGER NOT NULL DEFAULT 0"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_deletion_warning_at TIMESTAMPTZ"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS returns_enabled BOOLEAN"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS expected_amount INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS is_upgrade BOOLEAN NOT NULL DEFAULT FALSE"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS upgrade_products INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS upgrade_groups INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payment_requests ADD COLUMN IF NOT EXISTS upgrade_price INTEGER"
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
        await conn.exec_driver_sql(
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS photo_url TEXT"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS product_id VARCHAR(64)"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS product_category VARCHAR(128)"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS delivered_chat_ids TEXT NOT NULL DEFAULT '[]'"
        )
        await conn.exec_driver_sql(
            """CREATE TABLE IF NOT EXISTS linked_groups (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                chat_id BIGINT NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )"""
        )
        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_linked_groups_user_id ON linked_groups(user_id)"
        )
        await conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_linked_groups_chat_id ON linked_groups(chat_id)"
        )
        # Eski bitta-guruh ustunidagi ma'lumotni yangi jadvalga ko'chirish
        await conn.exec_driver_sql(
            """INSERT INTO linked_groups (user_id, chat_id)
               SELECT id, linked_group_chat_id FROM users
               WHERE linked_group_chat_id IS NOT NULL
               ON CONFLICT (chat_id) DO NOTHING"""
        )

"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def init_db():
    """Initialize database and create tables."""
    from database.models import Camera, User
    from utilities.auth import get_password_hash
    from sqlalchemy import select
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    
    # Create admin user if it doesn't exist
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(User).where(User.username == settings.admin_username))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                admin = User(
                    username=settings.admin_username,
                    email=settings.admin_email,
                    hashed_password=get_password_hash(settings.admin_password),
                    is_active=True,
                    is_admin=True
                )
                session.add(admin)
                await session.commit()
                logger.info(f"✅ Admin user created - Username: {settings.admin_username}")
                logger.warning("⚠️ CHANGE THE ADMIN PASSWORD!")
            else:
                logger.info("Admin user already exists")
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            await session.rollback()


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

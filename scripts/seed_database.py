"""
Seed initial users for local development and demos.
"""
import asyncio
from app.core.security import hash_password
from app.db.database import AsyncSessionLocal, init_db
from app.db.models import User
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        users = [
            {"email": "admin@company.com", "password": "AdminPass123!", "role": "ADMIN"},
            {"email": "engineer@company.com", "password": "EngPass123!", "role": "ENGINEER"},
            {"email": "employee@company.com", "password": "EmpPass123!", "role": "EMPLOYEE"},
        ]
        for u in users:
            existing = await session.execute(
                __import__("sqlalchemy").select(User).where(User.email == u["email"])
            )
            if existing.scalar_one_or_none():
                logger.info("User already exists: %s", u["email"])
                continue
            user = User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
            )
            session.add(user)
            logger.info("Created user: %s (%s)", u["email"], u["role"])
        await session.commit()
    logger.info("Seeding complete")


if __name__ == "__main__":
    asyncio.run(seed())
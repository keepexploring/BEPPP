#!/usr/bin/env python3
"""
Quick script to create admin2 user for testing
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from models import User
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://beppp:beppp@localhost:5432/beppp")

async def create_admin():
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=True)

    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin2")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("✅ User 'admin2' already exists!")
            return

        # Create new admin user
        hashed_password = pwd_context.hash("admin2123")

        new_user = User(
            username="admin2",
            email="admin2@test.com",
            password_hash=hashed_password,
            first_name="Admin",
            last_name="Two",
            role="admin",
            is_active=True
        )

        session.add(new_user)
        await session.commit()

        print("✅ Successfully created admin2 user!")
        print("   Username: admin2")
        print("   Password: admin2123")

if __name__ == "__main__":
    asyncio.run(create_admin())

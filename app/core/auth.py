from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_async_session
from app.models import User
from app.core.enums import UserRole

auth_header = APIKeyHeader(name="Authorization", auto_error=True)


async def get_api_key(api_key_header: str = Depends(auth_header)) -> str:
    try:
        scheme, _, key = api_key_header.partition(" ")
        if scheme.lower() != "token":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return key.strip()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная схема авторизации",
        )


async def get_user(
    token: str = Depends(get_api_key),
    db_session: AsyncSession = Depends(get_async_session),
) -> User:
    query = select(User).where(User.api_key == token)
    result = await db_session.execute(query)
    current_user = result.scalars().first()

    if not current_user or current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или отсутствующий API ключ"
        )

    return current_user


async def for_admin(user: User = Depends(retrieve_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён: только для администраторов"
        )
    return user

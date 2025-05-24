from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import for_admin
from app.core.db import get_async_session
from app.crud.v1.user import user_crud
from app.models import ErrorMessage
from app.schemas.user import User

router = APIRouter()


@router.delete(
    '/admin/user/{user_id}',
    response_model=User,
    tags=['admin'],
    dependencies=[Depends(for_admin)],
    responses={
        200: {'description': 'User deleted successfully'},
        404: {
            'description': 'User not found',
            'model': ErrorMessage,
            'content': {
                'application/json': {
                    'example': {'detail': 'User not found'}
                }
            },
        },
    },
)
async def delete_user(
        user_id: UUID,
        session: AsyncSession = Depends(get_async_session),
):
    try:
        deleted_user = await user_crud.remove(user_id, session)
        return User.from_orm(deleted_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера delete_user: {str(e)}")

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from . import utils, models
from core.dependency import get_db
from sqlalchemy.sql.expression import select
from core.authorization import BaseAuthorization

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/user/token',  auto_error=False)


class JWTAuthorization(BaseAuthorization):
    async def __call__(self, db: AsyncSession = Depends(get_db), token=Depends(oauth2_scheme)) -> None:
        if token is None:
            user = None
        else:
            try:
                payload = utils.decode_access_token(token)
                id: str = payload.get("id")
            except JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not decode JWT token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            query = select(models.User).filter_by(id=id)
            user = await db.scalar(query)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not Find User",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return user

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from core.dependency import get_db

from . import serializers
from . import models
from . import utils



@router.get('/info')
async def info(request: Request):
    return request.state.user

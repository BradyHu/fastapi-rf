from fastapi import APIRouter
from . import account
from . import sms

router = APIRouter(prefix="/user")
# 公网注册登录
router.include_router(sms.router)
# 内网注册登录
router.include_router(account.router)

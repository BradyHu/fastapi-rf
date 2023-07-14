from fastapi import APIRouter
from . import account
from . import sms
from . import info
from . import wxapp

router = APIRouter(prefix="/user")
# 公网注册登录
router.include_router(sms.router)
router.include_router(wxapp.router)
# 内网注册登录
router.include_router(account.router)
# 用户信息
router.include_router(info.router)
from fastapi import APIRouter
from . import account
from . import sms

router = APIRouter()
router.include_router(account.router)
router.include_router(sms.router)

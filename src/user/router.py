from fastapi import APIRouter
from pydantic import BaseModel
from enum import Enum

router = APIRouter(
    prefix='/user'
)


class SmsCodeAction(str, Enum):
    register = 'register'
    login = 'login'
    reset = 'reset'
    rebind = 'rebind'


class SmsCodeReq(BaseModel):
    mobile: str
    action: SmsCodeAction


@router.post('/sms/code')
def sms_code(request:SmsCodeReq):
    

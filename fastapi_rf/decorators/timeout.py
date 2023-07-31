from functools import wraps
import asyncio


# 只有daphne启动时，才是协程的，因此需要做单元测试时，需要绕过这个功能
def timeout(seconds=55, error_message='超时：请求花费时间过长，无法正常返回'):
    def decorated(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if not asyncio.iscoroutinefunction(func):
                    raise ValueError("async func required")
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                # print(result)
                # result = func(*args, **kwargs)
            except asyncio.TimeoutError:
                import traceback
                traceback.print_exc()
                raise ValueError(error_message)
            return result

        return wrapper

    return decorated



class BaseAuthorization:
    async def __call__(self, *args, **kwargs):
        raise NotImplementedError

SECRET_KEY = "hello world"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
DATABASE = {
    # "url": "postgresql+asyncpg://postgres:ctdna@192.168.100.2:7803/hello",
    "url": "sqlite+aiosqlite:///db.sqlite",
    "connect_args": {
        "check_same_thread": False
    }
}
# for keto
KETO_MAX_INDIRECTION_DEPTH = 32
# keto with sqlalchemy does not support CTE
KETO_USING_CTE = False
WXAPP_KEYS = {
    "gh_xxxx": {
        "wxapp_key": "xxx",
        "wxapp_secret": "xxx"
    }
}
REDIS_URL = "redis://:ctdna@localhost:7804"

SECRET_KEY = "hello world"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
DATABASE = {
    "url": "postgresql+asyncpg://postgres:ctdna@192.168.100.2:7803/hello",
    "connect_args": {
    }
}
# for keto
KETO_MAX_INDIRECTION_DEPTH = 32
KETO_USING_CTE = True

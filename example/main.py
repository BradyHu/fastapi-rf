from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel, Field

from config.database import DATABASE
from config.urls import register_urls
from fastapi_rf.models import Base

# init database, don't use it in product environment

app = FastAPI(dependencies=[
    # Depends(get_current_user)
])
register_urls(app)


class IndexResp(BaseModel):
    service: str = Field(examples=["ez-admin"])


@app.get('/')
def index() -> IndexResp:
    return {"service": 'ez-admin'}


@app.on_event("startup")
async def init_database():
    async with DATABASE.engine.begin() as conn:
        ...
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':
    config = uvicorn.Config(app, host='0.0.0.0', port=8000, reload=True)
    server = uvicorn.Server(config=config)
    server.run()

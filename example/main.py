from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel, Field
import user.views
import keto.views

from user.serializers import UserRead
# from config.database import DATABASE
# init database
# DATABASE.Base.metadata.create_all(DATABASE.engine)
app = FastAPI(dependencies=[
    # Depends(get_current_user)
])
app.include_router(user.views.router)
app.include_router(keto.views.router)


class IndexResp(BaseModel):
    service: str = Field(examples=["ez-admin"])
    user: UserRead | None


@app.get('/')
def index() -> IndexResp:
    return {"service": 'ez-admin'}


if __name__ == '__main__':
    config = uvicorn.Config(app, host='0.0.0.0', port=8000, reload=False)
    server = uvicorn.Server(config=config)
    server.run()

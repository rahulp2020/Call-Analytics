from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from api.exception import register_exception_handlers
# from api.auth import register_jwt_dependency
from Apis.call import router as call_router
from Apis.analytics import router as analytics_router
import Apis.setting as config
from Apis.auth import Auth, jwt_middleware
from Apis.schema import UserRequest, UserResponse

app = FastAPI(title=config.APP_TITLE, version=config.APP_VERSION)
app.middleware("http")(jwt_middleware)

app.include_router(call_router.router, prefix=config.CALL_ROUTER, tags=["Calls"])
app.include_router(analytics_router.router, prefix=config.ANALYTICS_ROUTER, tags=["Analytics"])


@app.post("/signin")
async def signin(user: UserRequest):
    token = Auth.create_token(user.dict())
    return UserResponse(name=user.name, token=token)


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Analytics API is running"}

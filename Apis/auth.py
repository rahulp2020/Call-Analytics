from Apis.setting import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import time
import jwt
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse


class Auth:
    @classmethod
    def create_token(cls, data: dict):
        try:
            payload = data.copy()
            payload["exp"] = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return token
        except Exception as e:
            raise HTTPException(status_code=500, detail="Token generation failed")

    @classmethod
    def verify_token(cls, token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


async def jwt_middleware(request: Request, call_next):
    if request.url.path in ["/signin"]:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})
    token = auth_header.split(" ")[1]
    try:
        Auth.verify_token(token)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    response = await call_next(request)
    return response

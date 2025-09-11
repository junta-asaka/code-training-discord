import uvicorn
from api.index import router as index_router
from api.login import router as login_router
from api.user import router as user_router
from database import create_tables
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from middleware import auth_session

app = FastAPI()

# ルーティング設定
app.include_router(index_router)
app.include_router(user_router)
app.include_router(login_router)


@app.on_event("startup")
async def startup_event():
    """サーバ起動時の処理"""

    print("startup event")
    # テーブル作成
    await create_tables()
    print("Creating tables...")


@app.middleware("http")
async def middleware(req: Request, call_next):
    """HTTPリクエストのミドルウェア

    Args:
        req (Request): HTTPリクエスト
        call_next (_type_): 次のミドルウェアまたはエンドポイントを呼び出す関数

    Returns:
        _type_: HTTPレスポンス
    """

    print(req.url.path)
    if req.url.path in ["/login", "/register", "/docs", "/openapi.json"]:
        return await call_next(req)
    if not await auth_session(req):
        return JSONResponse(status_code=401, content="Unauthorized")

    return await call_next(req)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)

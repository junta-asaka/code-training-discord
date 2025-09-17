import uvicorn
from api.friend import router as friend_router
from api.index import router as index_router
from api.login import router as login_router
from api.user import router as user_router
from database import create_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware import auth_session

app = FastAPI()

# CORS設定
origins = ["http://localhost:8000", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 認証ミドルウェアを適用
app.middleware("http")(auth_session)

# ルーティング設定
app.include_router(index_router)
app.include_router(user_router)
app.include_router(login_router)
app.include_router(friend_router)


@app.on_event("startup")
async def startup_event():
    """サーバ起動時の処理"""

    print("startup event")
    # テーブル作成
    await create_tables()
    print("Creating tables...")


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)

from contextlib import asynccontextmanager

import uvicorn
from api.channel import router as channel_router
from api.friend import router as friend_router
from api.login import router as login_router
from api.message import router as message_router
from api.user import router as user_router
from database import create_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware import auth_session
from utils.logger_utils import get_logger

# ロガーを取得
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    logger.info("アプリケーション起動処理を開始します")
    await create_tables()
    logger.info("データベーステーブルの作成が完了しました")

    yield

    # 終了時の処理（必要に応じて追加）
    logger.info("アプリケーションを終了します")


app = FastAPI(lifespan=lifespan)

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
app.include_router(user_router)
app.include_router(login_router)
app.include_router(friend_router)
app.include_router(channel_router)
app.include_router(message_router)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)

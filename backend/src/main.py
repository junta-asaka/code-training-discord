import uvicorn

# from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.index import router as index_router
from api.user import router as user_router
from database import create_tables


app = FastAPI()
app.include_router(index_router)
app.include_router(user_router)


@app.on_event("startup")
async def startup_event():
    print("startup event")
    await create_tables()  # サーバ起動時
    print("Creating tables...")


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Starting up...")
#     await create_tables()  # サーバ起動時
#     print("Creating tables...")
#     yield  # サーバ稼働中
#     # 終了時にクリーンアップしたい場合はここに追加


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)

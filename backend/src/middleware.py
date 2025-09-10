from database import get_session
from dependencies import get_injector
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from usecase.login import LoginUseCaseIf


def get_usecase(injector=Depends(get_injector)) -> LoginUseCaseIf:
    return injector.get(LoginUseCaseIf)


@app.middleware("http")
async def auth_session(
    req: Request,
    call_next,
    session: AsyncSession = Depends(get_session),
    usecase: LoginUseCaseIf = Depends(get_usecase),
):
    if req.url.path in ["/login", "/register"]:
        return await call_next(req)

    if not session:
        return RedirectResponse(url="/login")

    if not await usecase.auth_session(session, req):
        return RedirectResponse(url="/login")

    return await call_next(req)

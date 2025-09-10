from database import get_session
from dependencies import get_injector
from domains import Session
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schema.login_schema import LoginResponse
from usecase.login import LoginUseCaseIf

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_usecase(injector=Depends(get_injector)) -> LoginUseCaseIf:
    return injector.get(LoginUseCaseIf)


@router.post("/login", response_model=LoginResponse)
async def login(
    req: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session=Depends(get_session),
    usecase: LoginUseCaseIf = Depends(get_usecase),
):
    session_db: Session | None = await usecase.execute(session, req, form_data)

    if not session_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return LoginResponse(
        access_token=str(session_db.refresh_token_hash),
        token_type="bearer",
    )

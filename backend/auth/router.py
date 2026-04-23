from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import AuthContext, get_current_user
from backend.auth.schemas import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from backend.auth.service import login_user, logout_all, logout_user, refresh_tokens, register_user
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/10minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    response: Response,
    db_session: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    data = await register_user(
        db_session=db_session,
        email=payload.email,
        password=payload.password,
        response=response,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return RegisterResponse(**data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/10minute")
async def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db_session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    data = await login_user(
        db_session=db_session,
        email=payload.email,
        password=payload.password,
        response=response,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return TokenResponse(**data)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/hour")
async def refresh(
    request: Request,
    response: Response,
    db_session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    refresh_token = request.cookies.get("skillos_refresh")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    data = await refresh_tokens(
        db_session=db_session,
        refresh_token=refresh_token,
        response=response,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
    return TokenResponse(**data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/hour")
async def logout(
    request: Request,
    response: Response,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    refresh_token = request.cookies.get("skillos_refresh")
    await logout_user(
        db_session=db_session,
        access_jti=current_user.jti,
        access_exp=current_user.exp,
        user_id=str(current_user.user.id),
        refresh_token=refresh_token,
        response=response,
        ip_address=request.client.host if request.client else None,
    )
    return response


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/hour")
async def logout_all_sessions(
    request: Request,
    response: Response,
    current_user: AuthContext = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    await logout_all(
        db_session=db_session,
        access_jti=current_user.jti,
        access_exp=current_user.exp,
        user_id=str(current_user.user.id),
        response=response,
        ip_address=request.client.host if request.client else None,
    )
    return response

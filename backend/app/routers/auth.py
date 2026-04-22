import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.rate_limit import _login_limiter
from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.oidc import _pkce_pair, get_oidc_metadata, fetch_jwks, exchange_code, decode_id_token
from app.auth.password import hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models.user import PasswordResetToken, RefreshToken, User
from app.models.household import Household, HouseholdMember
from app.schemas.auth import ChangePasswordRequest, LoginRequest, PasswordResetConfirm, PasswordResetRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.email import send_email, _build_reset_email

router = APIRouter(prefix="/auth")


@router.get("/setup-status")
def setup_status(db: Session = Depends(get_db)):
    return {"needs_setup": db.query(User).count() == 0}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="registration_disabled")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="email_taken")
    is_first = db.query(User).count() == 0
    role = "admin" if (is_first and settings.FIRST_USER_IS_ADMIN) else "user"
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        role=role,
        language=settings.DEFAULT_LANGUAGE,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()

    household_name = "Mein Haushalt" if user.language == "de" else "My Household"
    now = datetime.now(timezone.utc)
    household = Household(
        name=household_name,
        owner_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(household)
    db.flush()

    db.add(HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        role="owner",
        created_at=now,
    ))
    user.active_household_id = household.id

    raw_refresh, refresh_hash = create_refresh_token()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires,
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db.refresh(user)
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    xff = request.headers.get("X-Forwarded-For", "")
    client_ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown")

    if _login_limiter.is_blocked(client_ip):
        raise HTTPException(status_code=429, detail="too_many_requests")

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        _login_limiter.record_failure(client_ip)
        raise HTTPException(status_code=401, detail="invalid_credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="account_disabled")
    user.last_login = datetime.now(timezone.utc)
    raw_refresh, refresh_hash = create_refresh_token()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires,
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="missing_refresh_token")
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt is None or rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="invalid_refresh_token")
    return TokenResponse(access_token=create_access_token(rt.user_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).delete()
        db.commit()
    response.delete_cookie("refresh_token")


@router.post("/change-password", status_code=200)
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="invalid_current_password")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}


@router.post("/password-reset/request", status_code=200)
async def password_reset_request(body: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()
        if settings.SMTP_HOST:
            reset_url = f"/#/reset-password?token={raw}"
            subject, body_text, body_html = _build_reset_email(user.language, reset_url)
            await send_email(user.email, subject, body_text, body_html)
    return {"ok": True}


@router.post("/password-reset/confirm", status_code=200)
async def password_reset_confirm(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    prt = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not prt or prt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="invalid_or_expired_token")
    user = db.get(User, prt.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="invalid_or_expired_token")
    user.password_hash = hash_password(body.new_password)
    db.delete(prt)
    db.commit()
    return {"ok": True}


@router.get("/oidc/enabled")
async def oidc_enabled():
    return {"enabled": settings.OIDC_ENABLED}


@router.get("/oidc/login")
async def oidc_login(request: Request, response: Response):
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=404, detail="oidc_not_enabled")
    metadata = await get_oidc_metadata()
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    cookie_val = f"{state}:{verifier}"
    redirect_uri = str(request.base_url) + "api/auth/oidc/callback"
    auth_url = (
        f"{metadata['authorization_endpoint']}"
        f"?response_type=code"
        f"&client_id={settings.OIDC_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=openid+email+profile"
        f"&state={state}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )
    resp = RedirectResponse(url=auth_url)
    resp.set_cookie("oidc_state", cookie_val, httponly=True, samesite="lax", max_age=600)
    return resp


@router.get("/oidc/callback")
async def oidc_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=404, detail="oidc_not_enabled")
    cookie_val = request.cookies.get("oidc_state", "")
    parts = cookie_val.split(":", 1)
    if len(parts) != 2 or parts[0] != state:
        raise HTTPException(status_code=400, detail="invalid_state")
    verifier = parts[1]
    metadata = await get_oidc_metadata()
    redirect_uri = str(request.base_url) + "api/auth/oidc/callback"
    token_data = await exchange_code(metadata["token_endpoint"], code, verifier, redirect_uri)
    jwks = await fetch_jwks(metadata["jwks_uri"])
    claims = decode_id_token(token_data["id_token"], jwks)
    sub = claims["sub"]
    email = claims.get("email", "")
    name = claims.get("name") or claims.get("preferred_username") or email.split("@")[0]

    user = db.query(User).filter(User.oidc_sub == sub).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.oidc_sub = sub
    if not user:
        is_first = db.query(User).count() == 0
        role = "admin" if (is_first and settings.FIRST_USER_IS_ADMIN) else "user"
        user = User(
            email=email,
            password_hash="",
            name=name,
            role=role,
            oidc_sub=sub,
            language=settings.DEFAULT_LANGUAGE,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(user.id)
    resp = RedirectResponse(url=f"/#/oidc-callback?access_token={access_token}")
    resp.delete_cookie("oidc_state")
    return resp

from fastapi import APIRouter, Depends, status, Body
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from controllers.users_ctrl import UserCtrl
from db.main import get_session 
from schemas.users_schema import EmailData, ResetPassword, ResetPasswordConfirm, ChangePassword

from utils.config import get_settings
from utils.auth.auth import create_access_token, hash_password, verify_password
from utils.auth.dependencies import RefreshTokenBearer, RoleChecker, get_current_user, AccessTokenBearer
from utils.errors import(
    UserNotFound, InvalidToken, PasswordsDoNotMatch,
    MustRoles, CannotModifySuperadmin, InvalidCredentials)

from utils.auth.mail import send_email
from utils.auth.auth import decode_url_token, generate_url_token
from utils.templates import render_template
from db.redis import add_jti_to_blocklist
from models import User

auth_router = APIRouter(prefix="/api/auth",tags=["Authentication & Authorization"])

superadmin_allowed = RoleChecker(["superadmin"])
user_allowed = RoleChecker(["user"])
user_ctrl = UserCtrl()
settings = get_settings()



@auth_router.get("/verify_email/{token}")
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_session)):

    # Verify the token/ decode it
    try:
        token_data = decode_url_token(token)
        user_email = token_data.get('email')
        
        if user_email:
            user = await user_ctrl.get_user(user_email, session)
            
            if not user:
                html_content = render_template("verification_error.html")
                return HTMLResponse(content=html_content, status_code=status.HTTP_404_NOT_FOUND)

            await user_ctrl.update_user_verify(user, {"is_verified": True}, session)
            html_content = render_template("verification_success.html")
            return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
        
        html_content = render_template("verification_error.html")
        return HTMLResponse(content=html_content, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception:
        html_content = render_template("verification_error.html")
        return HTMLResponse(content=html_content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@auth_router.get("/refresh_token")
async def new_access_token(
    token_details: dict = Depends(RefreshTokenBearer())
    ):

    expiry_timestamp = token_details['exp']
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(
            user_data = token_details['user']
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "New access token generated",
                "access_token": new_access_token
            }
        )
    raise InvalidToken()

@auth_router.post("/update_role", status_code=status.HTTP_200_OK)
async def update_user_role(
    email: str = Body(...),
    role: str = Body(...),
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(superadmin_allowed)):
    """Update a user's role. Only superadmin can call this."""

    if role not in ("user", "admin"):
        raise MustRoles()

    user = await user_ctrl.get_user(email, session)
    if not user:
        raise UserNotFound()

    if user.role == "superadmin":
        raise CannotModifySuperadmin()

    user.role = role
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return JSONResponse(
        content={"message": f"User '{email}' role updated to '{role}'"},
        status_code=status.HTTP_200_OK
        )


@auth_router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePassword,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):
    """Change password for the authenticated user. Requires current password."""

    if not verify_password(password_data.current_password, current_user.hash_password):
        raise InvalidCredentials()

    if password_data.new_password != password_data.confirm_new_password:
        raise PasswordsDoNotMatch()

    pwd_hash = hash_password(password_data.new_password)
    await user_ctrl.update_user_verify(current_user, {"hash_password": pwd_hash}, session)

    return JSONResponse(
        content={"message": "Password changed successfully"},
        status_code=status.HTTP_200_OK
    )


@auth_router.post("/revoke-all-sessions", status_code=status.HTTP_200_OK)
async def revoke_all_sessions(
    token_details: dict = Depends(AccessTokenBearer()),
    _: bool = Depends(user_allowed)):
    """Logout from all devices by revoking the current token.
    
    Note: For full multi-device logout, implement a per-user token version counter in Redis.
    This revokes the current session's token immediately.
    """
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={"message": "Current session revoked. Please logout from other devices manually."},
        status_code=status.HTTP_200_OK
    )


@auth_router.post("/reset_password")
async def reset_password(
    password_data: ResetPassword,
    session: AsyncSession = Depends(get_session)):
    """
    1. User requests password reset / provide the email
    2. Sends reset link to user's email
    3. Updates password / password confirmation
    """
    email = password_data.email

    user = await user_ctrl.get_user(email, session)
    if not user:
        raise UserNotFound()

    token_data = {"email": email}
    token = generate_url_token(token_data, salt="password-reset")
    subject = "Password Reset Request"
    reset_link = f"{settings.FRONTEND_URL}?reset_token={token}"
    html_message = render_template("password_reset.html", reset_link=reset_link)

    await send_email(recipients=[email], subject=subject, body=html_message)
    return JSONResponse(
        content={"message": "Please check your email to reset your password."},
        status_code=status.HTTP_200_OK
    )

@auth_router.post("/reset_password_confirm/{token}")
async def reset_account_password(
    token: str,
    password_data: ResetPasswordConfirm,
    session: AsyncSession = Depends(get_session)):

    new_password = password_data.new_password
    confirm_password = password_data.confirm_new_password

    if new_password != confirm_password:
        raise PasswordsDoNotMatch()

    token_data = decode_url_token(token, salt="password-reset")
    email = token_data.get("email")
    if not email:
        raise UserNotFound()

    user = await user_ctrl.get_user(email, session)
    if not user:
        raise UserNotFound()

    # Update password
    pwd_hash = hash_password(new_password)
    await user_ctrl.update_user_verify(user, {"hash_password": pwd_hash}, session)

    return JSONResponse(
        content={"message": "Password reset successfully"},
        status_code=status.HTTP_200_OK
    )

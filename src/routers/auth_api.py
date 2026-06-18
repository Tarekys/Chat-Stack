from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from controllers.users_ctrl import UserCtrl
from db.main import get_session 
from schemas.users_schema import EmailData, ResetPassword, ResetPasswordConfirm

from utils.config import get_settings
from utils.auth.auth import create_access_token, hash_password
from utils.auth.dependencies import RefreshTokenBearer,RoleChecker
from utils.errors import(
    UserNotFound, InvalidToken, PasswordsDoNotMatch,
    MustRoles, CannotModifySuperadmin)

from utils.auth.mail import send_email
from utils.auth.auth import decode_url_token, generate_url_token
from utils.templates import render_template

auth_router = APIRouter(prefix="/api/auth",tags=["auth"])

superadmin_allowed = RoleChecker(["superadmin"])
user_ctrl = UserCtrl()
settings = get_settings()


@auth_router.post("/test-send-mail")
async def send_test_email(mail_data: EmailData):
    emails = mail_data.addresses
    subject = "Verification Email!"
    html_content = """
    <html>
        <body>
            <p>Hi there!</p>
            <p>Welcome to our application!</p>
        </body>
    </html>
    """

    await send_email(recipients=emails, subject=subject, body=html_content)
    return JSONResponse(
        content={"message": "Email sent successfully"},
        status_code=status.HTTP_200_OK
    )

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
    email: str,
    username: str,
    role: str,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(superadmin_allowed)):

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
    reset_link = f"http://{settings.APP_DOMAIN}/api/auth/reset_password_confirm/{token}"
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

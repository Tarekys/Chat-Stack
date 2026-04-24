import email
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from utils.auth.auth import create_access_token
from utils.config import get_settings
from utils.auth.dependencies import RefreshTokenBearer,RoleChecker
from controllers.users_ctrl import UserCtrl
from db.main import get_session 
from utils.errors import(
    UserNotFound, InvalidToken,
    MustRoles, CannotModifySuperadmin)
from utils.auth.mail import send_email
from schemas.users_schema import EmailData
from utils.auth.auth import decode_url_token

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
    token_data = decode_url_token(token)
    user_email = token_data.get('email')
    
    if user_email:
        user = await user_ctrl.get_user(user_email, session)
        
        if not user:
            raise UserNotFound()

        await user_ctrl.update_user_verify(user, {"is_verified": True}, session)
        return JSONResponse(
            content={"message": "Account verified successfully"},
            status_code=status.HTTP_200_OK
        )
    return JSONResponse(
        content={"message": "Error occurred while verifying account"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

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

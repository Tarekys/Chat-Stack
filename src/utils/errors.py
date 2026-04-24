from typing import Callable, Any
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status

class AppException(Exception):
    """Base class for all custom exceptions"""
    pass

class InvalidToken(Exception):
    """User has provided an invalid or expired token"""
    pass

class AccessTokenRequired(Exception):
    """User has provided a valid access token"""
    pass

class RefreshTokenRequired(Exception):
    """User has provided a valid refresh token"""
    pass

class NoPermission(Exception):
    """User does not have sufficient permissions to perform this action"""
    pass

class UserNotFound(Exception):
    """User has provided a token for a user that does not exist"""
    pass

class AccountNotVerified(Exception):
    """Account is not verified"""
    pass
#---------------------------------------------------------
class MustRoles(Exception):
    """User must have one of the specified roles"""
    pass

class CannotModifySuperadmin(Exception):
    """User cannot modify superadmin"""
    pass

class UserAlreadyExists(Exception):
    """User already exists"""
    pass

class InvalidCredentials(Exception):
    """Invalid credentials password or email"""
    pass

class MessageNotFound(Exception):
    """User is trying to access a message that does not exist"""
    pass

class ConversationNotFound(Exception):
    """User is trying to access a conversation that does not exist"""
    pass

class PasswordsDoNotMatch(Exception):
    """Passwords do not match"""
    pass

def create_error_response(status_code: int, detail: Any) -> Callable[[Request, Exception], JSONResponse]:

    async def error_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code= status_code,
            content= detail
        )
    return error_handler
    

def register_all_errors(app: FastAPI):
    app.add_exception_handler(
        InvalidToken,
        create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Invalid or expired token",
                "error_code": "invalid_token",
            },
        ),
    )
    app.add_exception_handler(
        AccessTokenRequired,
        create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Access token required",
                "error_code": "access_token_required",
            },
        ),
    )
    app.add_exception_handler(
        RefreshTokenRequired,
        create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token required",
                "error_code": "refresh_token_required",
            },
        ),
    )
    app.add_exception_handler(
        InvalidCredentials,
        create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Invalid credentials",
                "error_code": "invalid_credentials",
            },
        ),
    )
    app.add_exception_handler(
        NoPermission,
        create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "You are not allowed to perform this action. Insufficient permissions",
                "error_code": "no_permission",
            },
        ),
    )
    app.add_exception_handler(
        MustRoles,
        create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "User does not have the required roles",
                "error_code": "must_roles",
            },
        ),
    )
    app.add_exception_handler(
        CannotModifySuperadmin,
        create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Cannot modify superadmin",
                "error_code": "cannot_modify_superadmin",
            },
        ),
    )
    app.add_exception_handler(
        UserNotFound,
        create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "User not found",
                "error_code": "user_not_found",
            },
        ),
    )
    app.add_exception_handler(
        MessageNotFound,
        create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Message not found",
                "error_code": "message_not_found",
            },
        ),
    )
    app.add_exception_handler(
        ConversationNotFound,
        create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Conversation not found",
                "error_code": "conversation_not_found",
            },
        ),
    )
    app.add_exception_handler(
        UserAlreadyExists,
        create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "User already exists",
                "error_code": "user_already_exists",
            },
        ),
    )
    app.add_exception_handler(
        Exception,
        create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Oops! Something went wrong on our end. Please try again later.",
                "error_code": "internal_server_error",
            },
        ),
    )
    app.add_exception_handler(
        AccountNotVerified,
        create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Account is not verified",
                "error_code": "account_not_verified",
                "resolution": "Please verify your account using the verification link sent to your email",
            },
        )
    )
    app.add_exception_handler(
        PasswordsDoNotMatch,
        create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Passwords do not match",
                "error_code": "passwords_do_not_match",
            },
        )
    )
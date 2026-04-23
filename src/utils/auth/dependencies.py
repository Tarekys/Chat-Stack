# for Autherzition we used dependency injection
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from .auth import decode_token
from db.redis import token_in_blocklist
from db.main import get_session
from controllers import users_ctrl
from sqlmodel.ext.asyncio.session import AsyncSession
from models import User
from typing import Any, List
from ..errors import (
     InvalidToken, RefreshTokenRequired, NoPermission,
     AccessTokenRequired)

ROLE_HIERARCHY = {
    "superadmin": {"superadmin", "admin", "user"},
    "admin":      {"admin", "user"},
    "user":       {"user"}
}

user_ctrl = users_ctrl.UserCtrl()

class TokenBearer(HTTPBearer):
     def __init__(self, auto_error = True):
          super().__init__(auto_error=auto_error)
     
     async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
          crads = await super().__call__(request)

          token = crads.credentials

          token_data = decode_token(token)

          if not self.token_valid(token):
               raise InvalidToken()

          if await token_in_blocklist(jti = token_data['jti']):
               raise InvalidToken()

          self.verify_token(token_data)

          # if we reach here, the token is valid and verified
          return token_data


     def token_valid(self, token: str) -> bool:
          token_data = decode_token(token)
          if token_data:
               return True
          else:
               return False

     def verify_token(self, token_data):
          raise NotImplementedError(
               "Please implement this method in subclass"
          )

class AccessTokenBearer(TokenBearer):

     def verify_token(self, token_data: dict) -> None:
          if token_data and token_data['refresh']:
               raise AccessTokenRequired()

class RefreshTokenBearer(TokenBearer):

     def verify_token(self, token_data: dict) -> None:
          if token_data and not token_data['refresh']:
               raise RefreshTokenRequired()

async def get_current_user(
     token_data: dict = Depends(AccessTokenBearer()),
     session: AsyncSession = Depends(get_session)
     ) -> dict:

     user_email = token_data['user']['email']
     user = await user_ctrl.get_user(user_email, session)
     return user

class RoleChecker:
     def __init__(self, allowed_roles: List[str]):
          self.allowed_roles = set(allowed_roles)
     
     def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
          user_roles = ROLE_HIERARCHY.get(current_user.role, set())
          if user_roles & self.allowed_roles:
               return True

          raise NoPermission()
          
## Pre-defined role checkers
# checker_any = RoleChecker(["user", "admin", "superadmin"])
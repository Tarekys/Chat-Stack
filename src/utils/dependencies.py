# for Autherzition we used dependency injection
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from .auth import decode_token

class TokenBearer(HTTPBearer):
     def __init__(self, auto_error = True):
          super().__init__(auto_error=auto_error)
     
     async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
          crads = await super().__call__(request)

          token = crads.credentials

          token_data = decode_token(token)

          if not self.token_valid:
               raise HTTPException(
                    status_code= status.HTTP_403_FORBIDDEN,
                    detail= "Token is invalid or expired"
                    )
          
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
               raise HTTPException(
                    status_code= status.HTTP_403_FORBIDDEN,
                    detail= "Please provide an access token"
                    )

class RefreshTokenBearer(TokenBearer):

     def verify_token(self, token_data: dict) -> None:
          if token_data and not token_data['refresh']:
               raise HTTPException(
                    status_code= status.HTTP_403_FORBIDDEN,
                    detail= "Please provide a refresh token"
                    )

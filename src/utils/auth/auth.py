import bcrypt
from datetime import timedelta, datetime
import jwt
import uuid
from ..config import get_settings
import logging
from itsdangerous import URLSafeTimedSerializer
from ..errors import InvalidToken

settings = get_settings()

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode('utf-8')[:72]
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)

def create_access_token(user_data: dict, expiry: timedelta= None, refresh: bool = False):
    payload = {}

    payload['user'] = user_data
    payload['exp'] = datetime.now() + (
        expiry if expiry else timedelta(seconds=settings.ACCESS_TOKEN_EXPIRY)
    )
    payload['jti'] = str(uuid.uuid4()) # jwt id
    payload['refresh'] = refresh
    
    token = jwt.encode(
        payload = payload, 
        key = settings.JWT_SECRET_KEY, 
        algorithm = settings.JWT_ALGORITHM
    )
    return token
 
def decode_token(token: str) -> dict | None:
    try:
        token_data = jwt.decode(
            jwt = token,
            key = settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return token_data

    except jwt.PyJWTError as exc:
        logging.error(f"Token decoding failed: {exc}")
        return None


salt = "email-verification"
serializer = URLSafeTimedSerializer(
        secret_key = settings.JWT_SECRET_KEY,
        salt = salt
    )
def generate_url_token(data:dict, salt:str = salt):
    token = serializer.dumps(data, salt=salt)
    return token

def decode_url_token(token: str, salt: str = salt):
    try:
        token_data = serializer.loads(token, salt=salt)
        if not token_data:
            raise InvalidToken()

        return token_data

    except Exception as exc:
        logging.error(f"Token verification failed: {exc}")
        raise InvalidToken()

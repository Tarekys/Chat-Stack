from redis.asyncio import Redis
from redis.exceptions import ConnectionError
from utils.config import get_settings
import logging

settings = get_settings()

token_blocklist = Redis(
    host= settings.REDIS_HOST,
    port= settings.REDIS_PORT,
    db= 0
)

_redis_available = None
async def _check_redis():
    global _redis_available
    try:
        await token_blocklist.ping()
        if _redis_available is not True:
            logging.info("Redis connected successfully.")
            _redis_available = True
        return True
    except ConnectionError:
        if _redis_available is not False:
            logging.warning("Redis not available. Token blocklist disabled.")
            _redis_available = False
        return False


async def add_jti_to_blocklist(jti: str):
    if not await _check_redis():
        return
    await token_blocklist.set(
        name= jti,
        value= "true",
        ex= settings.ACCESS_TOKEN_EXPIRY  # 1 hour expiration
    )

async def token_in_blocklist(jti: str) -> bool:
    if not await _check_redis():
        return False
    jti_value = await token_blocklist.get(jti)
    return jti_value is not None
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from ..config import get_settings
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME= settings.MAIL_USERNAME,
    MAIL_PASSWORD= settings.MAIL_PASSWORD,
    MAIL_FROM= settings.MAIL_FROM,
    MAIL_PORT= settings.MAIL_PORT,
    MAIL_SERVER= settings.MAIL_SERVER,
    MAIL_FROM_NAME= settings.MAIL_FROM_NAME,
    MAIL_STARTTLS= True,
    MAIL_SSL_TLS= False,
    USE_CREDENTIALS= True,
    VALIDATE_CERTS= True,
    TEMPLATE_FOLDER = Path(BASE_DIR, "templates")
)

mail = FastMail(config=conf)

async def send_email(recipients: List[str], subject: str, body: str):
    message = MessageSchema(
        subject = subject,
        recipients = recipients,
        body = body,
        subtype = MessageType.html
    )
    await mail.send_message(message)

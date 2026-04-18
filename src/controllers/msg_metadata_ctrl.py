from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlmodel import select, desc

from models.msg_metadata import MessageMetadata

from schemas.msg_metadata_schema import (
    MessageMetadataCreate,
    MessageMetadataUpdate
)
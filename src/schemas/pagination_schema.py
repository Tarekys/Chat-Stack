"""
Pagination:
- تقسيم البيانات الكبيرة إلى صفحات صغيرة بدل ما ترجعها كلها مرة واحدة
- لو عندي محادثة فيها رسائل بالمئات وعند استدعاء الAPI هيرجعهم كلهم مرة واحدة
     - لذلك الحل: GET /messages/1?limit=20&offset=0
     - تحديد العدد limit=20
     - تحديد نقطة البداية offset=0
     - تحديد العدد لزيادة الكفاءة و تجنب المشاكل
"""

from typing import List
from pydantic import BaseModel
from .messages_schema import MessageRead

class PaginatedMessages(BaseModel):
    total: int
    items: List[MessageRead]
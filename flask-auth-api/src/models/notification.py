from typing import Optional

from pydantic import BaseModel


class Message(BaseModel):
    notification_name: str
    user_id: str
    template_id: Optional[str]
    content_id: Optional[str]
    content_value: Optional[str]

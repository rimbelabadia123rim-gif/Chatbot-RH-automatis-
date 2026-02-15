# backend/app/models/base.py

from pydantic import BaseModel
from datetime import datetime

class BaseModelWithTimestamp(BaseModel):
    created_at: datetime
    updated_at: datetime

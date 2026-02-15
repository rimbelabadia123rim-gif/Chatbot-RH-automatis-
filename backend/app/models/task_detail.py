from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class TaskDetail(Base):
    __tablename__ = 'task_details'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    field_name = Column(String)
    field_value = Column(String)
    created_at = Column(String)
    updated_at = Column(String)

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_type = Column(String)
    status = Column(String)
    task_description = Column(String)
    requested_at = Column(String)
    completed_at = Column(String)
    created_at = Column(String)
    updated_at = Column(String)

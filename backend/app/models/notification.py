from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # 'conge_valide', 'conge_refuse', 'info', etc.
    is_read = Column(Boolean, default=False)
    related_id = Column(Integer, nullable=True)  # ID de la demande de congé concernée
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation avec User
    user = relationship("User", back_populates="notifications")

from app.database import Base  # Correction de l'importation
from sqlalchemy import Column, Integer, String, Text

class Instruction(Base):
    __tablename__ = 'instructions'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(String)
    updated_at = Column(String)
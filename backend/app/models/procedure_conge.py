from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class ProcedureConge(Base):
    __tablename__ = "procedure_conge"
    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    delai = Column(String, nullable=True)  # Exemple : "48h avant le début du congé"

from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base
from datetime import datetime

class DemandeConge(Base):
    __tablename__ = "demandes_conge"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    type_conge = Column(String(50), nullable=False)
    date_debut = Column(DateTime, nullable=False)
    date_fin = Column(DateTime, nullable=False)
    raison = Column(Text, nullable=True)
    status = Column(String(50), default="en attente")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    preuve = Column(String(255), nullable=True)  # Chemin du fichier justificatif

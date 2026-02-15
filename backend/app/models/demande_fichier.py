from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class DemandeFichier(Base):
    __tablename__ = "demande_fichier"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fichier_csv = Column(String, nullable=False)
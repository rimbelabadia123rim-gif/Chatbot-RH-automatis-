from app.models.demande_conge import DemandeConge
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

def create_demande_conge(db: Session, user_id: int, type_conge: str, date_debut: datetime, date_fin: datetime, raison: Optional[str] = None, preuve: Optional[str] = None):
    demande = DemandeConge(
        user_id=user_id,
        type_conge=type_conge,
        date_debut=date_debut,
        date_fin=date_fin,
        raison=raison,
        preuve=preuve,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(demande)
    db.commit()
    db.refresh(demande)
    return demande

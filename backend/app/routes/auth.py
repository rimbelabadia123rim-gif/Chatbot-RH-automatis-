from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

router = APIRouter()

@router.post("/login")
def login(matricule: str, db: Session = Depends(get_db)):
    # Vérifier si le matricule existe dans la base de données
    user = db.query(User).filter(User.matricule == matricule).first()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Retourner un message ou un token (ici, juste un message pour simplifier)
    return {"message": f"Bienvenue {user.first_name} {user.last_name}"}

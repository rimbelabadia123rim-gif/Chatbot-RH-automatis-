from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.demande_conge import DemandeConge
from app.models.user import User
from app.services.notification_service import create_conge_validation_notification
import os

router = APIRouter()

@router.get("/admin/demandes-conge")
async def get_all_demandes_conge(request: Request, db: Session = Depends(get_db)):
    # Authentification basique par header (à adapter selon votre auth réelle)
    matricule = request.headers.get("X-User-Matricule")
    if not matricule:
        raise HTTPException(status_code=401, detail="Matricule requis dans les headers.")
    user = db.query(User).filter(User.matricule == matricule).first()
    if not user or user.department.upper() != "RH":
        raise HTTPException(status_code=403, detail="Accès réservé au département RH.")
    demandes = db.query(DemandeConge).all()
    result = []
    for d in demandes:
        demandeur = db.query(User).filter(User.id == d.user_id).first()
        result.append({
            "id": d.id,
            "user": {
                "matricule": demandeur.matricule if demandeur else None,
                "first_name": demandeur.first_name if demandeur else None,
                "last_name": demandeur.last_name if demandeur else None
            },
            "type_conge": d.type_conge,
            "date_debut": d.date_debut.strftime('%Y-%m-%d'),
            "date_fin": d.date_fin.strftime('%Y-%m-%d'),
            "raison": d.raison,
            "status": d.status,
            "created_at": d.created_at.strftime('%Y-%m-%d %H:%M'),
            "preuve": d.preuve
        })
    return JSONResponse(content={"demandes": result})

@router.post("/admin/demandes-conge/{demande_id}/status")
async def update_demande_status(demande_id: int, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    new_status = data.get("status")
    if new_status not in ["validé", "refusé"]:
        raise HTTPException(status_code=400, detail="Status invalide.")
    demande = db.query(DemandeConge).filter(DemandeConge.id == demande_id).first()
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée.")
    
    # Sauvegarder l'ancien statut pour éviter les notifications en double
    old_status = demande.status
    demande.status = new_status
    db.commit()
    
    # Créer une notification seulement si le statut a changé
    if old_status != new_status:
        create_conge_validation_notification(
            db=db,
            user_id=demande.user_id,
            demande_id=demande.id,
            status=new_status,
            demande_type=demande.type_conge
        )
    
    return JSONResponse(content={"success": True, "message": f"Statut mis à jour et notification envoyée."})

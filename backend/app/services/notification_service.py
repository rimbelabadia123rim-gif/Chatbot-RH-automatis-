from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.user import User
from datetime import datetime
from typing import List, Optional

def create_notification(
    db: Session, 
    user_id: int, 
    title: str, 
    message: str, 
    notification_type: str,
    related_id: Optional[int] = None
) -> Notification:
    """Créer une nouvelle notification pour un utilisateur"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        related_id=related_id,
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def get_user_notifications(db: Session, user_id: int, unread_only: bool = False) -> List[Notification]:
    """Récupérer les notifications d'un utilisateur"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).all()

def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    """Marquer une notification comme lue"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if notification:
        notification.is_read = True
        db.commit()
        return True
    return False

def mark_all_notifications_as_read(db: Session, user_id: int) -> int:
    """Marquer toutes les notifications d'un utilisateur comme lues"""
    count = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return count

def get_unread_count(db: Session, user_id: int) -> int:
    """Compter les notifications non lues d'un utilisateur"""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()

def create_conge_validation_notification(db: Session, user_id: int, demande_id: int, status: str, demande_type: str):
    """Créer une notification spécifique pour la validation/refus de congé"""
    if status.lower() == "validé":
        title = "✅ Demande de congé validée"
        message = f"Votre demande de congé ({demande_type}) a été validée par les RH. Vous pouvez consulter les détails dans votre historique."
        notif_type = "conge_valide"
    elif status.lower() == "refusé":
        title = "❌ Demande de congé refusée"
        message = f"Votre demande de congé ({demande_type}) a été refusée par les RH. Contactez le service RH pour plus d'informations."
        notif_type = "conge_refuse"
    else:
        title = "📝 Statut de demande mis à jour"
        message = f"Le statut de votre demande de congé ({demande_type}) a été mis à jour : {status}"
        notif_type = "conge_update"
    
    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notif_type,
        related_id=demande_id
    )

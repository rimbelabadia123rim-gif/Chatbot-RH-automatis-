# Script de test pour le système de notifications
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_db
from app.models.user import User
from app.models.demande_conge import DemandeConge
from app.services.notification_service import create_conge_validation_notification
from datetime import datetime

def test_notification_system():
    """Test du système de notifications"""
    # Simuler une session de base de données
    db = next(get_db())
    
    try:
        # Trouver un utilisateur test
        user = db.query(User).first()
        if not user:
            print("❌ Aucun utilisateur trouvé pour le test")
            return
            
        print(f"✅ Utilisateur trouvé: {user.first_name} {user.last_name} (ID: {user.id})")
        
        # Créer une demande de congé test
        test_demande = DemandeConge(
            user_id=user.id,
            type_conge="test",
            date_debut=datetime.now(),
            date_fin=datetime.now(),
            raison="Test du système de notifications",
            status="en attente"
        )
        
        db.add(test_demande)
        db.commit()
        db.refresh(test_demande)
        
        print(f"✅ Demande de congé créée (ID: {test_demande.id})")
        
        # Tester la notification de validation
        notification = create_conge_validation_notification(
            db=db,
            user_id=user.id,
            demande_id=test_demande.id,
            status="validé",
            demande_type="test"
        )
        
        print(f"✅ Notification de validation créée (ID: {notification.id})")
        print(f"   Titre: {notification.title}")
        print(f"   Message: {notification.message}")
        
        # Tester la notification de refus
        notification_refus = create_conge_validation_notification(
            db=db,
            user_id=user.id,
            demande_id=test_demande.id,
            status="refusé",
            demande_type="test"
        )
        
        print(f"✅ Notification de refus créée (ID: {notification_refus.id})")
        print(f"   Titre: {notification_refus.title}")
        print(f"   Message: {notification_refus.message}")
        
        # Nettoyer les données de test
        db.delete(notification)
        db.delete(notification_refus)
        db.delete(test_demande)
        db.commit()
        
        print("✅ Données de test nettoyées")
        print("🎉 Test du système de notifications réussi !")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_notification_system()

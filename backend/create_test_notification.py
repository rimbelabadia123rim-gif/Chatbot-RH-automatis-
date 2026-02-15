#!/usr/bin/env python3
"""
Script pour créer une notification de test afin de vérifier le frontend
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.notification_service import create_notification

def create_test_notification():
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Trouver un utilisateur de test (prendre le premier)
        user = db.query(User).first()
        if not user:
            print("Aucun utilisateur trouvé dans la base de données")
            return
        
        print(f"Création d'une notification de test pour l'utilisateur: {user.first_name} {user.last_name} (matricule: {user.matricule})")
        
        # Créer une notification de test
        notification = create_notification(
            db=db,
            user_id=user.id,
            title="Test de notification",
            message="Ceci est une notification de test pour vérifier que le système fonctionne correctement.",
            notification_type="test",
            related_id=None
        )
        
        if notification:
            print(f"✅ Notification de test créée avec succès (ID: {notification.id})")
            print(f"Titre: {notification.title}")
            print(f"Message: {notification.message}")
        else:
            print("❌ Erreur lors de la création de la notification")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_notification()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour initialiser les procédures de congé dans la base de données
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.procedure_conge import ProcedureConge
from app.models.base import Base

def create_sample_procedures():
    """Créer des procédures de congé d'exemple"""
    
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Vérifier si des procédures existent déjà
        existing = db.query(ProcedureConge).first()
        if existing:
            print("Des procédures existent déjà dans la base de données.")
            return
        
        # Créer les procédures de congé
        procedures = [
            ProcedureConge(
                titre="Congés payés annuels",
                description="Pour les congés payés annuels, vous devez faire votre demande au moins 1 mois à l'avance. Fournissez les dates de début et fin, ainsi qu'une justification. Un document de planification peut être demandé pour les périodes de forte activité.",
                delai="1 mois avant le début du congé"
            ),
            ProcedureConge(
                titre="Congé maladie",
                description="Pour un congé maladie, vous devez fournir un certificat médical dans les 48h suivant le début de l'arrêt. Envoyez le document par email à votre manager et aux RH. Pour les arrêts de plus de 3 jours, un certificat de prolongation peut être nécessaire.",
                delai="48h après le début de l'arrêt maladie"
            ),
            ProcedureConge(
                titre="Congé exceptionnel",
                description="Les congés exceptionnels (mariage, naissance, décès) doivent être demandés dès que possible avec les justificatifs appropriés. Les délais légaux s'appliquent selon le motif. Contactez les RH pour connaître vos droits selon votre situation.",
                delai="Dès que possible avec justificatifs"
            ),
            ProcedureConge(
                titre="RTT (Réduction du Temps de Travail)",
                description="Les RTT peuvent être posées avec un préavis de 2 semaines minimum. Vérifiez votre solde disponible et assurez-vous que votre charge de travail permet votre absence. L'accord de votre manager est requis.",
                delai="2 semaines minimum"
            ),
            ProcedureConge(
                titre="Congé sans solde",
                description="Les congés sans solde nécessitent une demande écrite motivée adressée à la direction, avec un préavis de 2 mois minimum. L'accord est soumis à l'étude de votre dossier et aux besoins du service.",
                delai="2 mois minimum"
            )
        ]
        
        # Ajouter les procédures à la base
        for procedure in procedures:
            db.add(procedure)
        
        db.commit()
        print(f"✅ {len(procedures)} procédures de congé ont été créées avec succès!")
        
        # Afficher les procédures créées
        print("\nProcédures créées :")
        for proc in procedures:
            print(f"- {proc.titre}")
            print(f"  Délai: {proc.delai}")
            print(f"  Description: {proc.description[:100]}...")
            print()
            
    except Exception as e:
        print(f"❌ Erreur lors de la création des procédures : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_procedures()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour voir les barres de progression vertes en action
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.main import create_progress_bar

def test_barres_vertes():
    """Teste l'affichage des barres vertes avec différents pourcentages"""
    
    print("🧪 TEST DES BARRES DE PROGRESSION VERTES")
    print("=" * 60)
    print()
    
    # Test avec différents pourcentages
    pourcentages = [0, 15, 30, 45, 60, 75, 90, 100]
    
    print("📊 APERÇU DES DIFFÉRENTS NIVEAUX :")
    print("-" * 40)
    
    for pct in pourcentages:
        barre = create_progress_bar(pct, width=15)
        
        # Ajout d'un commentaire selon le niveau
        if pct >= 80:
            niveau = "🟢 EXCELLENT"
        elif pct >= 60:
            niveau = "🟡 BON"
        elif pct >= 30:
            niveau = "🟠 MOYEN"
        else:
            niveau = "🔴 FAIBLE"
        
        print(f"{niveau:15} | {barre}")
    
    print()
    print("📈 EXEMPLE D'UTILISATION DANS LES RAPPORTS :")
    print("-" * 50)
    
    # Simulation de données de rapport
    types_conges = [
        ("Congés payés", 85),
        ("RTT", 65),
        ("Congé maladie", 45),
        ("Congé exceptionnel", 25)
    ]
    
    for type_conge, pourcentage in types_conges:
        barre = create_progress_bar(pourcentage, width=12)
        print(f"• {type_conge:20} : {barre}")
    
    print()
    print("✅ TEST TERMINÉ - Les barres vertes sont opérationnelles !")
    print("💡 Elles seront affichées dans :")
    print("   - Les rapports de congés")
    print("   - L'explication des pourcentages d'acceptation")
    print("   - Les statistiques RH")

if __name__ == "__main__":
    test_barres_vertes()

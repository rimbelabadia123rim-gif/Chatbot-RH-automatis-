#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test d'accuracy pour le modèle de détection d'intention du chatbot
Avec barres de progression vertes pour la visualisation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.main import detect_intent, create_progress_bar
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pandas as pd

# Jeu de données de test avec exemples et leurs intentions attendues
TEST_DATA = [
    # Salutations
    ("bonjour", "greeting"),
    ("salut", "greeting"),
    ("hello", "greeting"),
    ("coucou", "greeting"),
    ("bjr", "greeting"),
    ("hi", "greeting"),
    
    # Politesse
    ("merci", "politeness"),
    ("thank you", "politeness"),
    ("thanks", "politeness"),
    ("mrc", "politeness"),
    
    # Questions sur le rôle
    ("quel est ton rôle", "role_query"),
    ("qui es-tu", "role_query"),
    ("tu fais quoi", "role_query"),
    ("ta mission", "role_query"),
    ("t qui", "role_query"),
    
    # Questions sur l'état
    ("comment ça va", "status_query"),
    ("ça va", "status_query"),
    ("comment vas-tu", "status_query"),
    ("cava", "status_query"),
    ("cv", "status_query"),
    ("comment allez vous", "status_query"),
    
    # Historique/logs
    ("mes logs", "chat_history"),
    ("historique de chat", "chat_history"),
    ("affiche mes logs", "chat_history"),
    
    # Liste des congés RH
    ("liste des congés", "liste_conges_rh"),
    ("demandes de congé", "liste_conges_rh"),
    ("historique des congés", "liste_conges_rh"),
    ("suivi des congés", "liste_conges_rh"),
    
    # Suivi personnel des congés
    ("mes congés", "suivi_mes_conges"),
    ("suivi de mes congés", "suivi_mes_conges"),
    ("mes demandes de congé", "suivi_mes_conges"),
    ("statut de ma demande", "suivi_mes_conges"),
    ("ma dernière demande", "suivi_mes_conges"),
    
    # Demandes de congé
    ("je veux poser un congé", "demande_conge"),
    ("demande de congé", "demande_conge"),
    ("vacances", "demande_conge"),
    ("absence", "demande_conge"),
    ("congé", "demande_conge"),
    
    # Explication pourcentage
    ("pourquoi ce pourcentage", "explain_percentage"),
    ("détail du calcul", "explain_percentage"),
    ("explication du pourcentage", "explain_percentage"),
    ("comment ce pourcentage", "explain_percentage"),
    
    # Procédures congé
    ("procedure pour les congés", "procedure_conge"),
    ("comment poser un congé", "procedure_conge"),
    ("delai congé", "procedure_conge"),
    ("documents congé", "procedure_conge"),
    ("procedure congé", "procedure_conge"),
    ("comment faire une demande", "procedure_conge"),
    ("étapes pour congé", "procedure_conge"),
    ("marche à suivre", "procedure_conge"),
    
    # Prévision charge
    ("prévision charge", "workload_forecast"),
    ("charge de travail", "workload_forecast"),
    ("analyse charge", "workload_forecast"),
    ("missions en cours", "workload_forecast"),
    
    # Messages sans intention claire (doivent retourner None)
    ("test", None),
    ("abc", None),
    ("1234", None),
    ("", None),
    ("blablabla", None),
]

def test_model_accuracy():
    """
    Teste l'accuracy du modèle de détection d'intention
    """
    print("🧪 DÉMARRAGE DU TEST D'ACCURACY DU MODÈLE")
    print("=" * 60)
    
    # Extraire les inputs et les labels attendus
    test_inputs = [data[0] for data in TEST_DATA]
    expected_labels = [data[1] for data in TEST_DATA]
    
    # Faire les prédictions
    print("📊 Prédiction en cours...")
    predicted_labels = []
    
    for i, input_text in enumerate(test_inputs):
        try:
            prediction = detect_intent(input_text)
            predicted_labels.append(prediction)
            print(f"✓ {i+1:2d}/{len(test_inputs)} - '{input_text}' -> {prediction}")
        except Exception as e:
            print(f"❌ Erreur sur '{input_text}': {e}")
            predicted_labels.append(None)
    
    print("\n" + "=" * 60)
    
    # Calculer l'accuracy avec barre verte
    correct_predictions = sum(1 for pred, true in zip(predicted_labels, expected_labels) if pred == true)
    total_predictions = len(expected_labels)
    accuracy = correct_predictions / total_predictions
    accuracy_percentage = accuracy * 100
    
    print(f"📈 RÉSULTATS D'ACCURACY:")
    print(f"   Prédictions correctes: {correct_predictions}/{total_predictions}")
    
    # Affichage avec barre verte
    barre_accuracy = create_progress_bar(accuracy_percentage, width=25)
    print(f"   Accuracy globale: {barre_accuracy}")
    
    # Évaluation du niveau avec emoji
    if accuracy_percentage >= 95:
        niveau = "🟢 EXCELLENT"
        commentaire = "Le modèle est très performant !"
    elif accuracy_percentage >= 85:
        niveau = "🟡 BON"
        commentaire = "Le modèle fonctionne bien avec quelques améliorations possibles."
    elif accuracy_percentage >= 70:
        niveau = "🟠 ACCEPTABLE"
        commentaire = "Le modèle est fonctionnel mais nécessite des améliorations."
    else:
        niveau = "🔴 FAIBLE"
        commentaire = "Le modèle nécessite des améliorations importantes."
    
    print(f"   Niveau: {niveau}")
    print(f"   Évaluation: {commentaire}")
    
    # Analyser les erreurs
    errors = []
    for i, (pred, true) in enumerate(zip(predicted_labels, expected_labels)):
        if pred != true:
            errors.append({
                'input': test_inputs[i],
                'expected': true,
                'predicted': pred
            })
    
    if errors:
        print(f"\n❌ ERREURS DÉTECTÉES ({len(errors)}):")
        print("-" * 60)
        for error in errors:
            print(f"   Input: '{error['input']}'")
            print(f"   Attendu: {error['expected']}")
            print(f"   Prédit: {error['predicted']}")
            print()
    else:
        print("\n✅ AUCUNE ERREUR DÉTECTÉE!")
    
    # Rapport détaillé par classe avec barres
    print("\n📊 RAPPORT DÉTAILLÉ PAR INTENTION:")
    print("-" * 80)
    
    # Compter les prédictions par classe
    unique_labels = set(expected_labels + predicted_labels)
    
    for label in sorted(unique_labels, key=lambda x: (x is None, x)):
        if label is None:
            label_str = "None (pas d'intention)"
        else:
            label_str = label
            
        expected_count = expected_labels.count(label)
        predicted_count = predicted_labels.count(label)
        correct_count = sum(1 for p, e in zip(predicted_labels, expected_labels) 
                          if p == label and e == label)
        
        if expected_count > 0:
            precision = (correct_count / expected_count) * 100 if expected_count > 0 else 0
            barre_precision = create_progress_bar(precision, width=15)
            print(f"   {label_str:25} | Attendu: {expected_count:2d} | Correct: {correct_count:2d}")
            print(f"   {'':25} | Précision: {barre_precision}")
            print()
    
    return accuracy, errors

def test_edge_cases():
    """
    Teste des cas limites pour valider la robustesse
    """
    print("\n🔍 TEST DES CAS LIMITES:")
    print("-" * 40)
    
    edge_cases = [
        "BONJOUR",  # Majuscules
        "bonjour!",  # Ponctuation
        "   salut   ",  # Espaces
        "cong congé congés",  # Mots multiples
        "je veux voir mes congés historique",  # Intentions multiples
        "blabla congé blabla",  # Mot clé noyé
    ]
    
    for case in edge_cases:
        prediction = detect_intent(case)
        print(f"   '{case}' -> {prediction}")

def main():
    """
    Fonction principale
    """
    print("🤖 TEST D'ACCURACY DU MODÈLE DE DÉTECTION D'INTENTION")
    print("=" * 80)
    
    # Test principal
    accuracy, errors = test_model_accuracy()
    
    # Tests de cas limites
    test_edge_cases()
    
    # Recommandations avec barres
    print(f"\n💡 RECOMMANDATIONS:")
    print("-" * 50)
    
    accuracy_percentage = accuracy * 100
    
    if accuracy >= 0.95:
        print("   ✅ Excellent! Le modèle a une très bonne accuracy.")
        barre_recommandation = create_progress_bar(100, width=20)
        print(f"   Statut du modèle: {barre_recommandation}")
    elif accuracy >= 0.85:
        print("   ✅ Bon! Le modèle fonctionne bien.")
        print("   💡 Considérez d'ajouter plus d'exemples pour les classes avec erreurs.")
        barre_recommandation = create_progress_bar(85, width=20)
        print(f"   Statut du modèle: {barre_recommandation}")
    elif accuracy >= 0.70:
        print("   ⚠️  Acceptable mais peut être amélioré.")
        print("   💡 Ajoutez plus de mots-clés ou d'exemples d'entraînement.")
        barre_recommandation = create_progress_bar(70, width=20)
        print(f"   Statut du modèle: {barre_recommandation}")
    else:
        print("   ❌ Le modèle nécessite des améliorations importantes.")
        print("   💡 Revisitez la logique de détection d'intention.")
        barre_recommandation = create_progress_bar(50, width=20)
        print(f"   Statut du modèle: {barre_recommandation}")
    
    if len(errors) > 0:
        error_rate = (len(errors) / len(TEST_DATA)) * 100
        barre_erreurs = create_progress_bar(100 - error_rate, width=15)
        print(f"   📝 Taux de réussite: {barre_erreurs}")
        print(f"   📝 Analysez les {len(errors)} erreurs pour améliorer le modèle.")
    
    print(f"\n📋 SUMMARY:")
    print(f"   Total d'exemples testés: {len(TEST_DATA)}")
    
    # Summary avec barre finale
    barre_finale = create_progress_bar(accuracy_percentage, width=30)
    print(f"   Accuracy finale: {barre_finale}")
    print(f"   Nombre d'erreurs: {len(errors)}")

if __name__ == "__main__":
    main()

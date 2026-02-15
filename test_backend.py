#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour vérifier la connectivité et les réponses du backend.
"""

import requests
import json

# Configuration
BACKEND_URL = "http://localhost:8000"

def test_backend_connection():
    """Test de base pour vérifier si le backend est accessible."""
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print(f"✅ Backend accessible - Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Backend non accessible - Serveur arrêté ou problème de port")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_chat_endpoint(matricule, message):
    """Test de l'endpoint chat avec un message spécifique."""
    try:
        payload = {
            "matricule": matricule,
            "message": message
        }
        
        response = requests.post(
            f"{BACKEND_URL}/chat/",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Request: {payload}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat response: {data.get('response', 'No response field')}")
            return data
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors du test chat: {e}")
        return None

def main():
    print("🔍 Test de connectivité backend...")
    
    # Test de base
    if not test_backend_connection():
        return
    
    # Tests avec différents messages
    test_cases = [
        ("1", "bonjour"),  # Test de base
        ("1", ""),         # Test connexion
        ("1", "congé"),    # Test intention demande congé
        ("1", "email"),    # Test info utilisateur
    ]
    
    for matricule, message in test_cases:
        print(f"\n🧪 Test: matricule={matricule}, message='{message}'")
        result = test_chat_endpoint(matricule, message)
        if result:
            print(f"✅ Succès")
        else:
            print(f"❌ Échec")

if __name__ == "__main__":
    main()

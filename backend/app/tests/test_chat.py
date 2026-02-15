# backend/app/tests/test_chat.py

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_chat_valid():
    # Utilisateur avec matricule valide
    response = client.post("/chat", json={"matricule": "U12345", "message": "Bonjour"})
    assert response.status_code == 200
    assert "response" in response.json()

def test_chat_invalid():
    # Utilisateur avec matricule invalide
    response = client.post("/chat", json={"matricule": "InvalidMatricule", "message": "Bonjour"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Utilisateur non trouvé"

import sys
import os

from fastapi.testclient import TestClient

# Ajoute le répertoire 'backend/app' au chemin de recherche des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app')))

from backend.app.main import app


client = TestClient(app)

def test_login_valid():
    response = client.post("/login", json={"matricule": "U12345"})
    assert response.status_code == 200
    assert response.json()["matricule"] == "U12345"

def test_login_invalid():
    response = client.post("/login", json={"matricule": "InvalidMatricule"})
    assert response.status_code == 401

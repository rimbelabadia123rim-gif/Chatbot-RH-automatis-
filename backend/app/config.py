# backend/app/config.py

import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

class Config:
    DB_USER = os.getenv("DB_USER", "chatbot_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "chatbot_password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "chatbot_db")

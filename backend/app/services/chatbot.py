from sqlalchemy.orm import Session
from models.chat_logs import ChatLog
from models.instruction import Instruction
from models.user import User
from database import get_db  # importez la fonction get_db pour obtenir la session de la DB

# Fonction pour obtenir l'utilisateur par son matricule
def get_user_by_matricule(db: Session, matricule: str):
    return db.query(User).filter(User.matricule == matricule).first()

# Fonction pour obtenir toutes les instructions
def get_instructions(db: Session):
    return db.query(Instruction).all()

# Fonction pour obtenir les instructions par mots-clés dans le titre
def get_instructions_by_keywords(db: Session, keywords: str):
    # Recherche insensible à la casse pour des mots-clés dans le titre
    return db.query(Instruction).filter(Instruction.title.ilike(f"%{keywords}%")).all()

# Fonction qui gère les messages et interagit avec la base de données
def handle_message(db: Session, user_matricule: str, message: str):
    # Recherche de l'utilisateur par son matricule
    user = get_user_by_matricule(db, user_matricule)
    if not user:
        return "Utilisateur non trouvé."

    # Log de l'interaction avec l'utilisateur
    chat_log = ChatLog(user_id=user.id, message=message, sender="user", timestamp="2025-03-12 14:43:58")
    db.add(chat_log)
    db.commit()

    # Recherche d'instructions en utilisant des mots-clés extraits du message
    keywords = message.lower()  # Convertir le message en minuscules
    instructions = get_instructions_by_keywords(db, keywords)

    if instructions:
        response = "Voici les instructions trouvées :\n"
        for instruction in instructions:
            response += f"- {instruction.title}: {instruction.description}\n"
        return response

    # Réponse par défaut si aucune instruction n'est trouvée
    return "Aucune instruction trouvée pour cette demande. Essayez une autre question."

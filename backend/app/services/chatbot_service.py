# backend/app/services/chatbot_service.py

from app.models.user import User

async def generate_chat_response(user: User, message: str) -> str:
    # Logique de génération de réponse pour le chatbot en fonction de l'utilisateur
    # Par exemple, ici, on répond simplement selon le matricule de l'utilisateur.
    
    if user.role == "admin":
        return "Bonjour Admin, comment puis-je vous aider?"
    
    if user.department == "tech":
        return "Salut, vous êtes dans le département technique! Que puis-je faire pour vous?"
    
    return "Bonjour, comment puis-je vous aider?"

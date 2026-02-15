# backend/app/routes/chat.py

from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.services.chatbot_service import generate_chat_response
from app.database import Database

router = APIRouter()

@router.post("/chat")
async def chat(matricule: str, message: str, db: Database = Depends()):
    # Récupérer l'utilisateur à partir de la base de données
    query = "SELECT * FROM users WHERE matricule = $1"
    user_data = await db.fetch(query, matricule)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    user = User(**dict(user_data[0]))
    
    # Générer une réponse du chatbot
    response = await generate_chat_response(user, message)
    
    return {"response": response}

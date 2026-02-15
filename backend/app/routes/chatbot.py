from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from chatbot import handle_message

router = APIRouter()

@router.post("/chatbot")
def chatbot_response(user_matricule: str, message: str, db: Session = Depends(get_db)):
    response = handle_message(db, user_matricule, message)
    return {"response": response}

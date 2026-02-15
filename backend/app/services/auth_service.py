# backend/app/services/auth_service.py

from app.database import Database
from app.models.user import User

async def authenticate_user(matricule: str, db: Database) -> User:
    query = "SELECT * FROM users WHERE matricule = $1"
    result = await db.fetch(query, matricule)
    if result:
        return User(**dict(result[0]))
    return None

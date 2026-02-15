# backend/app/middlewares/auth_middleware.py

from fastapi import Request, HTTPException
from app.database import Database
from app.services.auth_service import authenticate_user

class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request):
        matricule = request.headers.get("Matricule")
        if not matricule:
            raise HTTPException(status_code=401, detail="Matricule requis")
        
        db = Database()
        user = await authenticate_user(matricule, db)
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non authentifié")
        
        request.state.user = user
        response = await self.app(request)
        return response

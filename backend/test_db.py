# test_db_connection.py
import asyncpg
import asyncio

async def test_connection():
    conn = await asyncpg.connect(
        user='chatbot_user',
        password='chatbot_password',
        database='chatbot_db',
        host='localhost'  # Par défaut localhost
    )
    print("Connexion réussie à la base de données.")
    await conn.close()

asyncio.run(test_connection())

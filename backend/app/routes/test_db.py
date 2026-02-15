from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text

# Configuration de la base de données
SQLALCHEMY_DATABASE_URL = "postgresql://chatbot_user:chatbot_password@localhost/chatbot_db"

# Créer une instance de l'engine SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Créer une session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Déclarer la base pour les modèles SQLAlchemy
Base = declarative_base()

# Modèle pour la table `instructions`
class Instruction(Base):
    __tablename__ = 'instructions'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(String)
    updated_at = Column(String)

# Fonction pour tester la connexion à la base de données
def test_db_connection():
    try:
        # Créer une session
        db = SessionLocal()
        # Exécuter une requête simple pour vérifier la connexion
        db.execute(text("SELECT 1"))
        print("✅ Connexion à la base de données réussie.")
    except Exception as e:
        print("❌ Erreur de connexion à la base de données :", e)
    finally:
        db.close()

# Fonction pour afficher le contenu de la table `instructions`
def display_instructions():
    try:
        # Créer une session
        db = SessionLocal()
        # Récupérer toutes les instructions
        instructions = db.query(Instruction).all()
        if instructions:
            print("📊 Contenu de la table `instructions` :")
            for instruction in instructions:
                print(f"ID: {instruction.id}")
                print(f"Title: {instruction.title}")
                print(f"Description: {instruction.description}")
                print(f"Created At: {instruction.created_at}")
                print(f"Updated At: {instruction.updated_at}")
                print("-" * 40)
        else:
            print("ℹ️ Aucune instruction trouvée dans la table `instructions`.")
    except Exception as e:
        print("❌ Erreur lors de la récupération des instructions :", e)
    finally:
        db.close()

# Point d'entrée du script
if __name__ == "__main__":
    print("🔍 Test de la connexion à la base de données...")
    test_db_connection()

    print("\n🔍 Affichage du contenu de la table `instructions`...")
    display_instructions()
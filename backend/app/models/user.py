from sqlalchemy import Column, Integer, String, DECIMAL, Date
from app.database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    matricule = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    role = Column(String)
    department = Column(String)
    created_at = Column(String)
    updated_at = Column(String)

    # ✅ Champs ajoutés
    status = Column(String)  # statut de l'employé
    current_missions = Column(String)  # missions en cours
    missions_status = Column(String)   # état des missions
    solde_conges = Column(DECIMAL)  # Solde actuel de congés payés (en jours)
    solde_rtt = Column(DECIMAL)     # Solde actuel de RTT (en jours)
    statut_employe = Column(String) # Statut (CDI, CDD, Stagiaire, etc.)
    telephone = Column(String)      # Numéro de téléphone professionnel
    adresse = Column(String)        # Adresse professionnelle
    date_dernier_conge = Column(Date) # Date du dernier congé pris
    date_maj_solde = Column(Date)      # Date de mise à jour du solde

    # 🔁 Relations
    chat_logs = relationship('ChatLog', back_populates='user', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')

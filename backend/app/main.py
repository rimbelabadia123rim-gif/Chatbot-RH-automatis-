import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys
import logging
from spellchecker import SpellChecker  # Pour la correction orthographique
from difflib import get_close_matches  # Pour la similarité des mots



from app.database import get_db
from app.models.user import User
from app.models.instruction import Instruction
from app.models.chat_logs import ChatLog
from app.models.task import Task  # Import du modèle Task
from app.models.notification import Notification  # Import du modèle Notification
from app.crud.demande_conge import create_demande_conge
from app.routes.demande_conge_admin import router as demande_conge_admin_router
from app.services.notification_service import (
    get_user_notifications, 
    mark_notification_as_read, 
    mark_all_notifications_as_read,
    get_unread_count
)

# Configuration du logging pour éviter les problèmes d'encodage
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend/chatbot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Créez une instance de l'application FastAPI
app = FastAPI()
origins = [
    "http://localhost:3000",  # Adresse frontend
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GPT-2 et son tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

# Initialiser le correcteur ortho
spell = SpellChecker(language='fr')  # Utiliser le français

# Mapping des erreurs courantes
COMMON_MISTAKES = {
    "email": "email",
    "émail":"email",
    "emil": "email",
    "adresse mail": "email",
    "prénom": "first name",
    "nom": "last name",
    "date de mise à jour": "updated at",
    "ameil": "email",
    "eml": "email",
    "meil": "email",
    "date mise a jour": "updated at",
    "date mise à jour": "updated at",
    "rle": "role",
    "nm": "last name",
    "prnom": "first name",
    "prnm": "first name",
    "mail": "email",
    "logs": "logs",
    "info user": "info user",
"Hello":"Hello",
"hello":"Hello",
    "informations de l'user": "informations de l'user",
  "bjr":"bonjour",
    "user": "user",
  "cc":"coucou",
  "coucou":"coucou",
    "info": "info",
"cv":"ça va",   
    "department": "department",
    "rtt":"rtt",
    "maj":"maj",
    "cong":"cong",
    "oman":"omar",
    "bassine":"yassine",
    "omar":"omar",
    "rh":"rh",
    "RH":"RH",
    
}
# Dictionnaire de noms propres ....
PROPER_NOUNS = {
    "John", "Doe", "Jane", "Smith", "Emily", "Davis",
}

import re

def correct_spelling(message: str):
    corrected_words = []
    for word in message.split():
        # Vérifier si le mot est une erreur courante
        if word.lower() in COMMON_MISTAKES:
            corrected_words.append(COMMON_MISTAKES[word.lower()])
            continue
        # Vérifier si le mot est un nom propre (commence par une majuscule et est suivi de lettres minuscules)
        if re.match(r'^[A-Z][a-z]*$', word):
            corrected_words.append(word)
            continue
        # Vérifier si le mot est dans la liste des noms propres (insensible à la casse)
        if word.lower() in {name.lower() for name in PROPER_NOUNS}:
            corrected_words.append(word)
            continue
        # Corriger chaque mot
        corrected_word = spell.correction(word)
        if corrected_word is not None:
            corrected_words.append(corrected_word)
        else:
            corrected_words.append(word)  # Garder le mot original si aucune correction n'est trouvée
    return " ".join(corrected_words)

# Fonction pour récupérer un utilisateur par son matricule
def get_user_by_matricule(db: Session, matricule: str):
    return db.query(User).filter(User.matricule == matricule).first()

# Fonction pour récupérer un utilisateur par son nom
def get_user_by_name(db: Session, first_name: str, last_name: str):
    return db.query(User).filter(User.first_name.ilike(f"%{first_name}%"), User.last_name.ilike(f"%{last_name}%")).first()

# Fonction pour récupérer les logs de chat d'un utilisateur
def get_user_chat_logs(db: Session, user_id: int):
    logs = db.query(ChatLog).filter(ChatLog.user_id == user_id).all()
    # Retourner uniquement les messages
    return [log.message for log in logs]

# Fonction helper pour créer un ChatLog avec timestamp automatique
def create_chat_log(user_id: int, message: str, sender: str = "bot"):
    return ChatLog(
        user_id=user_id, 
        message=message, 
        sender=sender,
        timestamp=datetime.now().strftime('%d/%m/%Y %H:%M')
    )

# Fonction pour récupérer la description d'une instruction par des mots-clés
def get_instruction_by_keywords(db: Session, keywords: list):
    instructions_found = []
    for keyword in keywords:
        pass  # Correction : bloc vide pour éviter l'erreur d'indentation
    return instructions_found[0] if instructions_found else None

# Fonction pour vérifier les permissions de l'utilisateur
def has_permission(user: User, required_department: str):
    return user.department == required_department

# Fonction pour extraire le prénom et le nom de l'utilisateur cible
def extract_first_and_last_name(message: str):
    # Liste des mots à ignorer
    ignore_words = {"info", "user", "informations", "de", "l'utilisateur", "l'user", "les", "données", "details"}
    
    # Convertir le message en minuscules pour une comparaison insensible à la casse
    message_lower = message.lower()
    
    # Filtrer les mots à ignorer
    words = [word for word in message.split() if word.lower() not in ignore_words]
    
    # Si on a au moins deux mots restants, les considérer comme prénom et nom
    if len(words) >= 2:
        return words[-2], words[-1]  # Prénom et nom sont les deux derniers mots
    else:
        return None, None

# Fonction pour détecter l'intention
def detect_intent(message: str):
    # Normalisation simple : minuscule, suppression accents, espaces multiples
    import unicodedata, re
    def normalize(text):
        text = text.lower()
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    message = normalize(message)

    # Intention : Accompagnement RH pour l'évolution professionnelle
    evolution_rh_keywords = [
        "comment le service rh peut il accompagner les employes dans leur evolution professionnelle",
        "comment le service rh accompagne les employes dans leur evolution professionnelle",
        "accompagnement rh evolution professionnelle",
        "comment rh aide a evoluer",
        "comment rh aide a la promotion",
        "aide rh pour changer de poste",
        "aide rh pour formation"
    ]
    for kw in evolution_rh_keywords:
        if kw in message:
            return "evolution_rh"
    # Intention : Responsable du service RH
    responsable_rh_keywords = [
        "qui est le responsable du service rh",
        "responsable rh",
        "nom du responsable rh",
        "chef du service rh"
    ]
    for kw in responsable_rh_keywords:
        if kw in message:
            return "responsable_rh"
    # Intention : Horaires du service RH
    horaires_rh_keywords = [
        "horaires du service rh",
        "quels sont les horaires du service rh",
        "heures d'ouverture rh",
        "quand puis-je contacter le service rh",
        "disponibilite rh"
    ]
    for kw in horaires_rh_keywords:
        if kw in message:
            return "horaires_rh"
    # Intention : Comment contacter le service RH ?
    contacter_rh_keywords = [
        "comment contacter le service rh",
        "comment joindre le service rh",
        "contacter rh",
        "joindre rh"
    ]
    for kw in contacter_rh_keywords:
        if kw in message:
            return "contacter_rh_basic"
    # Intention : Rôle du service RH
    role_rh_keywords = [
        "a quoi sert le service des ressources humaines",
        "quel est le role du service rh",
        "role du service rh",
        "utilite du service rh",
        "pourquoi le service rh",
        "fonction du service rh"
    ]
    for kw in role_rh_keywords:
        if kw in message:
            return "role_rh"
    # Intention : Aide RH au quotidien (plus robuste)
    aide_rh_keywords = [
        "comment le service rh peut il aider les employes",
        "comment le service rh peut-il aider les employes",
        "comment le service rh peut il aider les employés",
        "comment le service rh peut-il aider les employés",
        "aide rh quotidien",
        "aide du service rh",
        "comment rh aide employes",
        "comment rh aide employés",
        "comment les rh aident les employés?"
    ]
    for kw in aide_rh_keywords:
        if kw in message:
            return "aide_rh_quotidien"

    # Normalisation simple : minuscule, suppression accents, espaces multiples
    import unicodedata, re
    def normalize(text):
        text = text.lower()
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    message = normalize(message)

    # Détection des salutations
    if any(word in message for word in ["bonjour", "salut", "coucou", "Hello", "Hi", "bjr", "cc"]):
        return "greeting"

    if any(word in message for word in ["merci", "thanks", "thank you", "mrc"]):
        return "politeness"
    # Détection des questions sur le rôle du bot
    if any(word in message for word in ["ton rôle", "ton role", "qui es-tu", "qui est tu", "tu fais quoi", "t qui", "tfq", "ta mission"]):
        return "role_query"

    # Détection des questions sur l'état du bot
    if any(word in message for word in ["comment ça va", "ça va", "comment vas-tu", "cava", "cv", "comment vas tu","comment allez vous","comment allez-vous"]):
        return "status_query"


    # Intention : Comment contacter un RH
    if any(kw in message for kw in [
        "comment contacter un rh", "comment je peux contacter un rh", "contacter rh", "joindre rh", "prendre contact rh", "contact rh", "parler à un rh", "parler rh", "appeler rh", "email rh", "mail rh", "téléphoner rh", "numéro rh", "numero rh", "adresse rh"
    ]):
        return "contact_rh"

    # Intention : Fournir les infos RH à contacter (plus robuste)
    infos_rh_keywords = [
        "info rh", "infos rh", "information rh", "informations rh", "coordonnees rh", "contact rh", "contacts rh",
        "fournissez les info des rh", "fournir infos rh", "qui contacter rh", "responsable rh", "service rh", "personne rh",
        "email rh", "mail rh", "adresse rh", "numero rh", "numéro rh", "telephone rh", "téléphone rh", "tel rh"
    ]
    for kw in infos_rh_keywords:
        if kw in message:
            return "infos_rh"

    # Détection des demandes d'historique
    if "logs" in message or "historique de chat" in message:
        return "chat_history"

    # Détection de la liste des congés par le RH (plus souple) - DOIT ÊTRE AVANT demande_conge
    if any(kw in message for kw in [
        "liste des cong", "liste de congés", "liste congés", "liste congé",
        "demandes de congé", "demandes congés", "demandes congé",
        "historique des congés", "historique congés",
        "suivi des congés", "suivi congés"
    ]):
        return "liste_conges_rh"
    # Détection du suivi personnel des congés (utilisateur normal)
    if any(kw in message for kw in [
        "suivi de mes congés", "suivi de mes conges", "mes congés", "mes demandes de congé",
        "historique de mes congés", "statut de mes congés", "suivi mes congés",
        "mes demandes", "statut de ma demande", "ma dernière demande"
    ]):
        return "suivi_mes_conges"
    
    # Détection des demandes de congé (plus général, doit venir après)
    if any(kw in message for kw in ["congé", "demande de congé", "demande congé", "vacances", "absence"]):
        return "demande_conge"

    # Détection de l'intention d'explication du pourcentage
    if any(kw in message for kw in ["pourquoi ce pourcentage", "pourquoi ce taux", "détail du calcul", "explication du pourcentage", "pourcentage d'acceptation", "comment ce pourcentage"]):
        return "explain_percentage"
    
    # Ajout intention procédure congé (retourne le nom de l'intention)
    if any(kw in message for kw in [
        "procedure pour les cong", "procedure pour poser un cong", "comment poser un cong", 
        "delai cong", "delai pour poser un cong", "delai de traitement cong", 
        "documents cong", "justificatif cong", "procedure conge", "procedure congé",
        "comment faire une demande", "étapes pour congé", "marche à suivre",
        "que faut-il faire", "comment procéder", "démarches congé"
    ]):
        return "procedure_conge"

    # Nouvelles intentions RH pour l'analyse de charge
    if any(kw in message for kw in [
        "prévision charge", "prévisions charge", "charge de travail", "prévision travail",
        "analyse charge", "prévision équipe", "charge équipe", "workload",
        "missions en cours", "analyse missions", "prévision missions"
    ]):
        return "workload_forecast"
    
    if any(kw in message for kw in [
        "surcharge équipe", "alerte surcharge", "équipe surchargée", "trop de travail",
        "explication surcharge", "pourquoi surcharge", "détail surcharge"
    ]):
        return "overload_alert"

    # Nouvelles intentions pour la génération de rapports
    if any(kw in message for kw in [
        "rapport analyse congé", "rapport demandes congés", "rapport détaillé congé",
        "générez un rapport analyse", "générer rapport congé", "rapport congés détaillé",
        "analyse détaillée congés", "rapport sur les congés"
    ]):
        return "generate_leave_report"
    
    if any(kw in message for kw in [
        "rapport charge travail", "rapport prévision charge", "rapport détaillé charge",
        "générez rapport charge", "générer rapport workload", "rapport charge détaillé",
        "analyse détaillée charge", "rapport sur la charge"
    ]):
        return "generate_workload_report"
    
    # Détection des demandes de téléchargement de rapport
    if "télécharger" in message or "télécharge" in message or "download" in message:
        return "download_report"

    # Si aucune intention n'est détectée, retourner None
    return None

# Fonction pour générer des réponses avec GPT-2
def handle_message_with_gpt2(message: str):
    inputs = tokenizer.encode(message, return_tensors="pt", truncation=True, padding=True)
    attention_mask = torch.ones(inputs.shape, device=inputs.device)

    outputs = model.generate(inputs, attention_mask=attention_mask, max_length=150, num_return_sequences=1, no_repeat_ngram_size=2, pad_token_id=tokenizer.eos_token_id)

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return response.strip()

# Fonction pour créer une tâche dans la base de données
def create_task(db: Session, user_id: int, task_type: str, task_description: str):
    new_task = Task(
        user_id=user_id,
        task_type=task_type,
        status="en cours",
        task_description=task_description,
        requested_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# Endpoint API pour recevoir un message et renvoyer une réponse
class MessageRequest(BaseModel):
    matricule: str
    message: str

# Endpoint API pour soumettre une tâche via le formulaire
class TaskFormRequest(BaseModel):
    matricule: str
    task_type: str
    task_description: str

@app.post("/submit-task/")
async def submit_task(
    matricule: str = Form(...),
    task_type: str = Form(...),
    task_description: str = Form(...),
    proof: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = get_user_by_matricule(db, matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

    # Gérer l'enregistrement du fichier preuve
    proof_path = None
    if proof:
        uploads_dir = "backend/app/uploads"
        import os
        os.makedirs(uploads_dir, exist_ok=True)
        file_ext = os.path.splitext(proof.filename)[1]
        filename = f"preuve_{user.id}_{int(datetime.now().timestamp())}{file_ext}"
        file_path = os.path.join(uploads_dir, filename)
        with open(file_path, "wb") as f:
            f.write(await proof.read())
        proof_path = file_path

    # Créer la tâche avec les détails fournis
    task = create_task(db, user.id, task_type, task_description)

    # Si c'est une demande de congé, enregistrer aussi dans demandes_conge
    if task_type.lower() in ["congé", "conge", "absence", "maladie", "annuel", "exceptionnel"]:
        from app.models.demande_conge import DemandeConge
        demande = DemandeConge(
            user_id=user.id,
            type_conge=task_type,
            date_debut=datetime.now(),  # À adapter si dates fournies
            date_fin=datetime.now(),    # À adapter si dates fournies
            raison=task_description,
            preuve=proof_path,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(demande)
        db.commit()

    # Réinitialiser l'état de la conversation
    chat_log = create_chat_log(user.id, "Tâche enregistrée avec succès. Comment puis-je vous aider maintenant ?")
    db.add(chat_log)
    db.commit()

    return JSONResponse(content={"response": "Votre tâche a été enregistrée avec succès. Comment puis-je vous aider maintenant ?", "task_id": task.id})

# Temporary memory to store conversation state for each user
temp_memory = {}

@app.post("/chat/")
async def chat(request: MessageRequest, db: Session = Depends(get_db)):
    # Corriger les fautes d'orthographe dans le message (et le rendre accessible avant toute détection d'intention)
    message = request.message.lower() if request.message else ""
    corrected_message = correct_spelling(message)
    logger.info(f"Message original : {request.message}")
    logger.info(f"Message corrigé : {corrected_message}")
    message = corrected_message

    # Intentions RH : contact et infos
    intent = detect_intent(message)
    if intent == "evolution_rh":
        response = (
            "Le service RH aide les employés à évoluer dans leur carrière en proposant des formations, en conseillant sur les possibilités de promotion et en aidant à identifier les compétences à développer. Il soutient aussi les employés qui souhaitent changer de poste ou améliorer leurs qualifications."
        )
        return JSONResponse(content={"response": response})
    if intent == "responsable_rh":
        response = (
            "Le responsable du service RH est Mme Khadija Benani. Vous pouvez la contacter pour toute question spécifique liée aux ressources humaines."
        )
        return JSONResponse(content={"response": response})
    if intent == "horaires_rh":
        response = (
            "Le service RH est disponible du lundi au vendredi, de 9h à 12h et de 14h à 17h. N'hésitez pas à les contacter pendant ces horaires pour toute demande."
        )
        return JSONResponse(content={"response": response})
    if intent == "contacter_rh_basic":
        response = (
            "Pour contacter le service RH, vous pouvez envoyer un email à KhadijaBenani@entreprise.com, appeler le +01 23 45 67 89, ou vous rendre au bureau situé au 2ème étage, porte 204."
        )
        return JSONResponse(content={"response": response})
    # Corriger les fautes d'orthographe dans le message (et le rendre accessible avant toute détection d'intention)
    message = request.message.lower() if request.message else ""
    corrected_message = correct_spelling(message)
    logger.info(f"Message original : {request.message}")
    logger.info(f"Message corrigé : {corrected_message}")
    message = corrected_message

    # Intentions RH : contact et infos
    intent = detect_intent(message)
    if intent == "role_rh":
        response = (
            "Le service des ressources humaines est essentiel au bon fonctionnement d’une entreprise. Il s’occupe de la gestion des employés, du recrutement, de la formation, du suivi des carrières et du bien-être au travail. Les RH veillent à l’application des règles, accompagnent les collaborateurs dans leurs démarches et favorisent un climat de confiance et d’épanouissement professionnel."
        )
        return JSONResponse(content={"response": response})
    if intent == "aide_rh_quotidien":
        response = (
            "Le service des ressources humaines joue un rôle essentiel dans la vie quotidienne des employés. Il accompagne chacun dans ses démarches administratives, répond aux questions sur la paie, les congés ou la formation, et veille au bien-être au travail. Le service RH est aussi là pour écouter, conseiller et soutenir les collaborateurs face aux difficultés ou pour les aider à évoluer dans leur carrière. N'hésitez pas à le solliciter pour toute demande ou besoin d'information."
        )
        return JSONResponse(content={"response": response})
    if intent == "contact_rh":
        response = (
            "📞 Pour contacter le service RH :\n"
            "   • Email : KhadijaBenani@entreprise.com\n"
            "   • Téléphone : + 01 23 45 67 89\n"
            "   • Bureau : 2ème étage, porte 204\n"
            "N'hésitez pas à les contacter pour toute question liée aux ressources humaines."
        )
        return JSONResponse(content={"response": response})
    if intent == "infos_rh":
        response = (
            "ℹ️ Voici les informations de contact du service RH :\n"
            "   • Responsable RH : Mme Khadija Benani\n"
            "   • Email : KhadijaBenani@entreprise.com\n"
            "   • Téléphone : + 01 23 45 67 89\n"
            "   • Horaires : 9h-12h / 14h-17h, du lundi au vendredi\n"
            "   • Bureau : 2ème étage, porte 204\n"
            "Pour toute demande, privilégiez l'email ou le téléphone."
        )
        return JSONResponse(content={"response": response})
    user = get_user_by_matricule(db, request.matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

    # Si le message est vide, c'est une demande d'authentification (connexion)
    if not request.message.strip():
        return JSONResponse(content={
            "response": f"Votre prénom est : {user.first_name}\nVotre nom est : {user.last_name}",
            "first_name": user.first_name,
            "last_name": user.last_name
        })

    # Corriger les fautes d'orthographe dans le message
    corrected_message = correct_spelling(request.message.lower())
    logger.info(f"Message original : {request.message}")
    logger.info(f"Message corrigé : {corrected_message}")

    message = corrected_message

    # Normalisation pour détection souple des intentions procédure/délai congé
    import unicodedata
    def normalize(text):
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        return text.lower()
    normalized_message = normalize(message)
    keywords_proc = [
        "procedure conge", "procedure pour poser un conge", "comment poser un conge",
        "delai conge", "delai pour poser un conge", "delai de traitement conge",
        "documents conge", "justificatif conge", "procedure cong", "procedure conges"
    ]
    if any(kw in normalized_message for kw in keywords_proc):
        from app.models.procedure_conge import ProcedureConge
        procedures = db.query(ProcedureConge).all()
        if not procedures:
            return JSONResponse(content={
                "response": "❌ 𝗔𝘂𝗰𝘂𝗻𝗲 𝗽𝗿𝗼𝗰𝗲́𝗱𝘂𝗿𝗲 𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́ 𝗻'𝗲𝘀𝘁 𝗲𝗻𝗿𝗲𝗴𝗶𝘀𝘁𝗿𝗲́𝗲 𝗱𝗮𝗻𝘀 𝗹𝗲 𝘀𝘆𝘀𝘁𝗲̀𝗺𝗲.\n\n" +
                           "📋 𝗩𝗼𝗶𝗰𝗶 𝗹𝗲𝘀 𝗶𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻𝘀 𝗴𝗲́𝗻𝗲́𝗿𝗮𝗹𝗲𝘀 𝘀𝘂𝗿 𝗹𝗲𝘀 𝗽𝗿𝗼𝗰𝗲́𝗱𝘂𝗿𝗲𝘀 𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́𝘀 :\n\n" +
                           "═══════════════════════════════════════════════════\n\n" +
                           "🏖️  𝗖𝗢𝗡𝗚𝗘́𝗦 𝗣𝗔𝗬𝗘́𝗦\n" +
                           "    • Demande à effectuer : 1 mois à l'avance minimum\n" +
                           "    • Documents requis : Aucun justificatif\n" +
                           "    • Traitement : Validation par le manager\n\n" +
                           "🏥  𝗖𝗢𝗡𝗚𝗘́ 𝗠𝗔𝗟𝗔𝗗𝗜𝗘\n" +
                           "    • Délai : Certificat médical sous 48h\n" +
                           "    • Documents requis : Arrêt de travail médical\n" +
                           "    • Traitement : Envoi immédiat aux RH\n\n" +
                           "⚡  𝗥𝗧𝗧 (𝗥𝗲́𝗰𝘂𝗽𝗲́𝗿𝗮𝘁𝗶𝗼𝗻 𝗱𝘂 𝗧𝗲𝗺𝗽𝘀 𝗱𝗲 𝗧𝗿𝗮𝘃𝗮𝗶𝗹)\n" +
                           "    • Préavis : 2 semaines minimum\n" +
                           "    • Documents requis : Aucun justificatif\n" +
                           "    • Traitement : Validation par le manager\n\n" +
                           "🎯  𝗖𝗢𝗡𝗚𝗘́ 𝗘𝗫𝗖𝗘𝗣𝗧𝗜𝗢𝗡𝗡𝗘𝗟\n" +
                           "    • Préavis : Variable selon la situation\n" +
                           "    • Documents requis : Justificatifs obligatoires\n" +
                           "    • Traitement : Étude au cas par cas\n\n" +
                           "═══════════════════════════════════════════════════\n\n" +
                           "📞 𝗕𝗲𝘀𝗼𝗶𝗻 𝗱'𝗮𝗶𝗱𝗲 ? Contactez les RH ou votre manager pour plus de détails."
            })
        
        response = "📋 𝗚𝗨𝗜𝗗𝗘 𝗖𝗢𝗠𝗣𝗟𝗘𝗧 𝗗𝗘𝗦 𝗣𝗥𝗢𝗖𝗘́𝗗𝗨𝗥𝗘𝗦 𝗗𝗘 𝗖𝗢𝗡𝗚𝗘́\n\n"
        response += "═══════════════════════════════════════════════════\n\n"
        
        for i, proc in enumerate(procedures, 1):
            # Choisir une icône selon le type de procédure
            if "maladie" in proc.titre.lower():
                icon = "🏥"
            elif "payé" in proc.titre.lower() or "annuel" in proc.titre.lower():
                icon = "🏖️"
            elif "rtt" in proc.titre.lower():
                icon = "⚡"
            elif "exceptionnel" in proc.titre.lower():
                icon = "🎯"
            else:
                icon = "📄"
            
            response += f"{icon}  𝗣𝗥𝗢𝗖𝗘́𝗗𝗨𝗥𝗘 : {proc.titre.upper()}\n"
            response += f"    📝 𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻 : {proc.description}\n"
            if proc.delai:
                response += f"    ⏰ 𝗗𝗲́𝗹𝗮𝗶 𝗿𝗲𝗾𝘂𝗶𝘀 : {proc.delai}\n"
            response += f"    📊 𝗣𝗿𝗼𝗰𝗲́𝗱𝗨𝗿𝗲 #{i}\n\n"
        
        response += "═══════════════════════════════════════════════════\n\n"
        response += "💡 𝗔𝗰𝘁𝗶𝗼𝗻𝘀 𝗿𝗮𝗽𝗶𝗱𝗲𝘀 :\n"
        response += "   • 📝 Tapez '𝗱𝗲𝗺𝗮𝗻𝗱𝗲 𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́' pour démarrer\n"
        response += "   • ❓ Tapez '𝗮𝗶𝗱𝗲' pour voir toutes les options\n"
        response += "   • 📊 Tapez '𝘀𝗼𝗹𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́' pour voir vos jours restants\n\n"
        response += "💬 𝗕𝗲𝘀𝗼𝗶𝗻 𝗱'𝗮𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝗰𝗲 ? L'équipe RH est à votre disposition !"
        
        return JSONResponse(content={"response": response})    # Récupérer le dernier log de l'utilisateur pour connaître l'état de la conversation
    last_log = db.query(ChatLog).filter(ChatLog.user_id == user.id).order_by(ChatLog.id.desc()).first()

    # Ensure temporary memory is initialized for the user
    if user.id not in temp_memory or not isinstance(temp_memory[user.id], dict):
        temp_memory[user.id] = {"step": None, "data": {}}
    if "step" not in temp_memory[user.id]:
        temp_memory[user.id]["step"] = None
    if "data" not in temp_memory[user.id]:
        temp_memory[user.id]["data"] = {}
    # Log the current state of the temporary memory for debugging
    logger.debug(f"Temporary memory for user {user.id}: {temp_memory[user.id]}")    # Gestion de l'intention procedure_conge AVANT tout flow mais après init temp_memory
    if detect_intent(message) == "procedure_conge" and temp_memory[user.id]["step"] is None:
        from app.models.procedure_conge import ProcedureConge
        procedures = db.query(ProcedureConge).all()
        if not procedures:
            return JSONResponse(content={
                "response": "❌ 𝗔𝘂𝗰𝘂𝗻𝗲 𝗽𝗿𝗼𝗰𝗲́𝗝𝗲 𝘀𝗽𝗲́𝗰𝗶𝗳𝗶𝗾𝘂𝗲 𝗻'𝗲𝘀𝘁 𝗰𝗼𝗻𝗳𝗶𝗴𝘂𝗿𝗲́𝗲 𝗱𝗮𝗻𝘀 𝗹𝗲 𝘀𝘆𝘀𝘁𝗲̀𝗺𝗲.\n\n" +
                           "📋 𝗚𝗨𝗜𝗗𝗘 𝗚𝗘́𝗡𝗘́𝗥𝗔𝗟 𝗗𝗘𝗦 𝗣𝗥𝗢𝗖𝗘́𝗗𝗨𝗥𝗘𝗦 𝗗𝗘 𝗖𝗢𝗡𝗚𝗘́\n\n" +
                           "═══════════════════════════════════════════════════\n\n" +
                           "🏖️  𝗖𝗢𝗡𝗚𝗘́𝗦 𝗣𝗔𝗬𝗘́𝗦\n" +
                           "    • 📅 𝗔𝗻𝘁𝗶𝗰𝗶𝗽𝗮𝘁𝗶𝗼𝗻 : 1 mois minimum à l'avance\n" +
                           "    • 📄 𝗗𝗼𝗰𝘂𝗺𝗲𝗻𝘁𝘀 : Aucun justificatif requis\n" +
                           "    • ✅ 𝗩𝗮𝗹𝗶𝗱𝗮𝘁𝗶𝗼𝗻 : Par votre manager direct\n" +
                           "    • 📊 𝗧𝗿𝗮𝗶𝘁𝗲𝗺𝗲𝗻𝘁 : 5-7 jours ouvrés\n\n" +
                           "🏥  𝗖𝗢𝗡𝗚𝗘́ 𝗠𝗔𝗟𝗔𝗗𝗜𝗘\n" +
                           "    • ⚡ 𝗨𝗿𝗴𝗲𝗻𝗰𝗲 : Certificat médical sous 48h\n" +
                           "    • 📋 𝗗𝗼𝗰𝘂𝗺𝗲𝗻𝘁𝘀 : Arrêt de travail obligatoire\n" +
                           "    • 📧 𝗘𝗻𝘃𝗼𝗶 : Immédiat aux RH et manager\n" +
                           "    • 🔄 𝗦𝘂𝗶𝘃𝗶 : Prolongation si nécessaire\n\n" +
                           "⚡  𝗥𝗧𝗧 (Récupération Temps de Travail)\n" +
                           "    • 📅 𝗣𝗿𝗲́𝗮𝘃𝗶𝘀 : 2 semaines minimum\n" +
                           "    • 📄 𝗗𝗼𝗰𝘂𝗺𝗲𝗻𝘁𝘀 : Aucun justificatif\n" +
                           "    • ✅ 𝗩𝗮𝗹𝗶𝗱𝗮𝘁𝗶𝗼𝗻 : Par votre manager\n" +
                           "    • 📊 𝗦𝗼𝗹𝗱𝗲 : Vérifiable dans votre profil\n\n" +
                           "🎯  𝗖𝗢𝗡𝗚𝗘́ 𝗘𝗫𝗖𝗘𝗣𝗧𝗜𝗢𝗡𝗡𝗘𝗟\n" +
                           "    • 📋 𝗝𝘂𝘀𝘁𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗳𝘀 : Documents obligatoires\n" +
                           "    • 🔍 𝗘́𝘁𝘂𝗱𝗲 : Cas par cas avec les RH\n" +
                           "    • ⏱️ 𝗗𝗲́𝗹𝗮𝗶 : Variable selon la situation\n" +
                           "    • 📞 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 : RH pour validation préalable\n\n" +
                           "═══════════════════════════════════════════════════\n\n" +
                           "📞 𝗦𝘂𝗽𝗽𝗼𝗿𝘁 : Contactez les RH pour toute question spécifique"
            })
        
        response = "📋 𝗣𝗥𝗢𝗖𝗘́𝗗𝗨𝗥𝗘𝗦 𝗗𝗘 𝗖𝗢𝗡𝗚𝗘́ 𝗖𝗢𝗡𝗙𝗜𝗚𝗨𝗥𝗘́𝗘𝗦\n\n"
        response += "═══════════════════════════════════════════════════\n\n"
        
        for i, proc in enumerate(procedures, 1):
            # Attribution d'icônes selon le type de procédure
            if "maladie" in proc.titre.lower():
                icon = "🏥"
                color = "🔴"
            elif "payé" in proc.titre.lower() or "annuel" in proc.titre.lower():
                icon = "🏖️"
                color = "🟢"
            elif "rtt" in proc.titre.lower():
                icon = "⚡"
                color = "🟡"
            elif "exceptionnel" in proc.titre.lower():
                icon = "🎯"
                color = "🟠"
            else:
                icon = "📄"
                color = "🔵"
            
            response += f"{color} {icon}  𝗣𝗥𝗢𝗖𝗘́𝗗𝗨𝗥𝗘 : {proc.titre.upper()}\n"
            response += f"    📝 𝗗𝗲𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻 :\n        {proc.description}\n"
            if proc.delai:
                response += f"    ⏰ 𝗗𝗲́𝗹𝗮𝗶 𝗮̀ 𝗿𝗲𝘀𝗽𝗲𝗰𝘁𝗲𝗿 : {proc.delai}\n"
            response += f"    🔢 𝗣𝗿𝗼𝗰𝗲́𝗱𝗨𝗿𝗲 #{i:02d}\n"
            response += "    ─────────────────────────────────────\n\n"
        
        response += "═══════════════════════════════════════════════════\n\n"
        response += "💡 𝗔𝗰𝘁𝗶𝗼𝗻𝘀 𝗿𝗮𝗽𝗶𝗱𝗲𝘀 :\n"
        response += "   • 📝 Tapez '𝗱𝗲𝗺𝗮𝗻𝗱𝗲 𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́' pour démarrer\n"
        response += "   • ❓ Tapez '𝗮𝗶𝗱𝗲' pour voir toutes les options\n"
        response += "   • 📊 Tapez '𝘀𝗼𝗹𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́' pour voir vos jours restants\n\n"
        response += "💬 𝗕𝗲𝘀𝗼𝗶𝗻 𝗱'𝗮𝘀𝘀𝗶𝘀𝘁𝗮𝗻𝗰𝗲 ? L'équipe RH est à votre disposition !"
        
        return JSONResponse(content={"response": response})

    # Démarrage du flow demande congé si intention détectée et pas déjà en cours
    if detect_intent(message) == "demande_conge" and temp_memory[user.id]["step"] is None:
        temp_memory[user.id]["step"] = "collect_type"
        temp_memory[user.id]["data"] = {"user_id": user.id}
        return JSONResponse(content={"response": "Quel est le type de congé souhaité ? (ex : annuel, maladie, exceptionnel)"})

    # Update the conversation flow to store collected data in temporary memory
    if temp_memory[user.id]["step"] == "collect_type":
        temp_memory[user.id]["data"]["type_conge"] = message
        temp_memory[user.id]["step"] = "collect_start_date"
        return JSONResponse(content={"response": "Merci. Quelle est la date de début du congé ? (format : AAAA-MM-JJ)"})

    if temp_memory[user.id]["step"] == "collect_start_date":
        temp_memory[user.id]["data"]["date_debut"] = message
        temp_memory[user.id]["step"] = "collect_end_date"
        return JSONResponse(content={"response": "Merci. Quelle est la date de fin du congé ? (format : AAAA-MM-JJ)"})

    if temp_memory[user.id]["step"] == "collect_end_date":
        temp_memory[user.id]["data"]["date_fin"] = message
        temp_memory[user.id]["step"] = "collect_reason"
        return JSONResponse(content={"response": "Merci. Quelle est la raison de votre congé ?"})

    import csv
    import os

    # Function to save collected data directly to a well-structured CSV file
    def save_to_csv_directly(data):
        csv_file = os.path.join("c:\\Users\\asus\\Desktop\\try\\backend\\app\\crud", "demandes_conge.csv")
        fieldnames = ["User ID", "Type de Congé", "Date de Début", "Date de Fin", "Raison"]

        try:
            # Check if the file exists
            file_exists = os.path.isfile(csv_file)

            with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                # Write the header only if the file is new
                if not file_exists:
                    writer.writeheader()

                # Write the collected data in a clean and structured format
                writer.writerow({
                    "User ID": data["user_id"],
                    "Type de Congé": data["type_conge"].capitalize(),
                    "Date de Début": data["date_debut"],
                    "Date de Fin": data["date_fin"],
                    "Raison": data["raison"].capitalize() if data["raison"] else "Non spécifiée"
                })
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture dans le fichier CSV : {e}")

    # Update the conversation flow to save data directly to the database and manage CSV files
    if temp_memory[user.id]["step"] == "collect_reason":
        temp_memory[user.id]["data"]["raison"] = message
        logger.debug(f"[DEBUG] Après saisie raison, mémoire temporaire : {temp_memory[user.id]}")
        temp_memory[user.id]["step"] = "upload_proof"
        return JSONResponse(content={
            "response": "Merci. Veuillez uploader un document justificatif pour votre demande de congé.",
            "requestFile": True
        })

    # Gestion de l'état de la conversation
    if last_log and "Est-ce que vous voulez que je le fasse pour vous ?" in last_log.message:
        if message == "non":
            # Réinitialiser l'état de la conversation
            chat_log = create_chat_log(user.id, "Conversation réinitialisée.")
            db.add(chat_log)
            db.commit()
            return JSONResponse(content={"response": "D'accord, comment puis-je continuer à vous aider ?"})
        elif message == "oui":
            # Récupérer le titre de l'instruction demandée
            task_type = last_log.message.split("\n")[0]  # Le titre est la première ligne du message
            # Enregistrer l'état de la conversation pour demander les détails
            chat_log = create_chat_log(user.id, f"Fournissez-moi les détails de la tâche pour : {task_type}")
            db.add(chat_log)
            db.commit()
            return JSONResponse(content={"response": f"Fournissez-moi les détails de la tâche pour : {task_type}", "show_form": True, "task_type": task_type})
        else:
            return JSONResponse(content={"response": "Veuillez répondre par 'oui' ou 'non'."})

    if last_log and "Fournissez-moi les détails de la tâche pour :" in last_log.message:
        # Récupérer le titre de l'instruction demandée
        task_type = last_log.message.split(": ")[1]
        # Retourner une réponse pour afficher le formulaire
        return JSONResponse(content={"response": "Veuillez remplir le formulaire pour enregistrer la tâche.", "show_form": True, "task_type": task_type})

    # Exemple de poursuite de la conversation selon l’étape
    if last_log and "Quel est le type de congé" in last_log.message:
        db.add(create_chat_log(user.id, message, "user"))
        db.commit()

        chat_log = create_chat_log(user.id, "Merci. Quelle est la date de début du congé ? (format : AAAA-MM-JJ)")
        db.add(chat_log)
        db.commit()
        return JSONResponse(content={"response": chat_log.message})

    # Gestion de la collecte des champs nécessaires pour la demande de congé
    if last_log and "Quelle est la date de début du congé" in last_log.message:
        collected_type = last_log.message.split("type de congé : ")[1] if "type de congé : " in last_log.message else None
        db.add(create_chat_log(user.id, message, "user"))
        db.commit()

        chat_log = create_chat_log(user.id, "Merci. Quelle est la date de fin du congé ? (format : AAAA-MM-JJ)")
        db.add(chat_log)
        db.commit()
        return JSONResponse(content={"response": chat_log.message})

    if last_log and "Quelle est la date de fin du congé" in last_log.message:
        collected_debut = last_log.message.split("date de début : ")[1] if "date de début : " in last_log.message else None
        # Correction du bug : compléter ou commenter la ligne incomplète
        # db.add(ChatLog(user_id=user.id, message=message))  # Ligne incomplète supprimée/corrigée
        db.add(create_chat_log(user.id, message, "user"))
        db.commit()

        chat_log = create_chat_log(user.id, "Merci. Quelle est la raison de votre congé ?")
        db.add(chat_log)
        db.commit()
        return JSONResponse(content={"response": chat_log.message})

    # Gestion de l'upload de fichier preuve
    if last_log and "Merci. Veuillez uploader un document justificatif pour votre demande de congé." in last_log.message:
        # L'upload du fichier est géré par l'endpoint /upload-proof/, donc ici on ne fait rien
        return JSONResponse(content={"response": "Veuillez utiliser le formulaire d'upload pour envoyer votre fichier justificatif."})

    # Détection de l'intention
    intent = detect_intent(message)

    # --- Bloc RH : liste structurée de toutes les demandes de congé ---
    if intent == "liste_conges_rh":
        if not has_permission(user, "HR") and not has_permission(user, "RH"):
            return JSONResponse(content={"response": "Désolé, vous n'avez pas l'accès à la liste des congés."})
        from app.models.demande_conge import DemandeConge
        from app.models.user import User as UserModel
        demandes = db.query(DemandeConge).order_by(DemandeConge.created_at.desc()).all()
        demandes_struct = []
        for d in demandes:
            # Récupérer prénom et nom de l'utilisateur
            utilisateur = db.query(UserModel).filter(UserModel.id == d.user_id).first()
            first_name = utilisateur.first_name if utilisateur else ""
            last_name = utilisateur.last_name if utilisateur else ""
            demandes_struct.append({
                "id": d.id,
                "user_id": d.user_id,
                "first_name": first_name,
                "last_name": last_name,
                "type_conge": d.type_conge,
                "date_debut": d.date_debut.strftime('%Y-%m-%d') if d.date_debut else "",
                "date_fin": d.date_fin.strftime('%Y-%m-%d') if d.date_fin else "",
                "raison": d.raison,
                "statut": getattr(d, 'status', getattr(d, 'statut', 'en attente')),
                "preuve": d.preuve,
                "created_at": d.created_at.strftime('%Y-%m-%d %H:%M') if d.created_at else ""
            })
        return JSONResponse(content={"demandes_conges_structurees": demandes_struct})

    # Réponses prédéfinies en fonction de l'intention
    if intent == "greeting":
        return JSONResponse(content={"response": "Bonjour ! Comment puis-je vous aider aujourd'hui ?"})
    elif intent == "politeness":
        return JSONResponse(content={"response": "Avec plaisir ! Comment puis-je vous aider ?"})
    elif intent == "role_query":
        return JSONResponse(content={"response": "Je suis un chatbot intelligent conçu pour vous aider avec vos questions et vos tâches."})
    elif intent == "status_query":
        return JSONResponse(content={"response": "Je vais bien, merci de demander ! Et vous ?"})
    elif intent == "chat_history":
        chat_logs = db.query(ChatLog).filter(ChatLog.user_id == user.id).order_by(ChatLog.id.asc()).all()
        if chat_logs:
            response = "📋 HISTORIQUE DE VOS CONVERSATIONS\n\n"
            
            # En-tête du tableau simple
            header = f"{'Date':<18} {'Auteur':<12} {'Message':<50}"
            separator = '-' * 82
            
            response += f"{header}\n{separator}\n"
            
            for log in chat_logs:
                # Formater la date
                if hasattr(log, 'timestamp') and log.timestamp:
                    if isinstance(log.timestamp, str):
                        date = log.timestamp[:16] if len(log.timestamp) > 16 else log.timestamp
                    else:
                        date = log.timestamp.strftime('%d/%m/%Y %H:%M')
                else:
                    date = "Non définie"
                
                # Formater l'auteur avec icônes
                if hasattr(log, 'sender') and log.sender:
                    if log.sender.lower() == 'user':
                        author = "👤 Vous"
                    elif log.sender.lower() == 'bot':
                        author = "🤖 Bot"
                    else:
                        author = f"⚙️ {log.sender.capitalize()}"
                else:
                    author = "⚙️ Système"
                
                # Formater le message
                if log.message:
                    message = log.message.replace('\n', ' ').replace('\r', ' ').strip()
                    # Nettoyer les espaces multiples
                    import re
                    message = re.sub(r'\s+', ' ', message)
                    
                    # Tronquer si trop long
                    if len(message) > 47:
                        message = message[:44] + "..."
                else:
                    message = "Message vide"
                
                # Assurer que les champs ne dépassent pas les largeurs
                date = date[:17]
                author = author[:11]
                message = message[:49]
                
                # Ligne du tableau
                response += f"{date:<18} {author:<12} {message:<50}\n"
            
            response += f"{separator}\n\n"
            
            # Statistiques finales
            response += f"📊 Total: {len(chat_logs)} message(s) dans votre historique\n"
            response += f"📅 Période: Du plus ancien au plus récent\n"
            response += f"💡 Conseil: Tapez 'nouveau chat' pour effacer l'historique"
            
            return JSONResponse(content={"response": response})
        else:
            return JSONResponse(content={"response": "Aucun historique de chat trouvé."})
    
    # 🔥 NOUVELLE FONCTIONNALITÉ : Suivi personnel des congés pour utilisateur normal
    elif intent == "suivi_mes_conges":
        from app.models.demande_conge import DemandeConge
        from app.models.user import User as UserModel
        
        # Récupérer toutes les demandes de congé de l'utilisateur connecté
        mes_demandes = db.query(DemandeConge).filter(DemandeConge.user_id == user.id).order_by(DemandeConge.created_at.desc()).all()
        
        if not mes_demandes:
            return JSONResponse(content={
                "response": "📋 𝗔𝘂𝗰𝘂𝗻𝗲 𝗱𝗲𝗺𝗮𝗻𝗱𝗲 𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́ 𝘁𝗿𝗼𝘂𝘃𝗲́𝗲\n\n" +
                           "Vous n'avez encore soumis aucune demande de congé.\n\n" +
                           "💡 Tapez 'demande congé' pour en créer une nouvelle."
            })
        
        response = f"📊 𝗠𝗘𝗦 𝗗𝗘𝗠𝗔𝗡𝗗𝗘𝗦 𝗗𝗘 𝗖𝗢𝗡𝗚𝗘́ ({len(mes_demandes)} au total)\n\n"
        response += "═══════════════════════════════════════════════════\n\n"
        
        for i, demande in enumerate(mes_demandes, 1):
            # Déterminer l'icône selon le type
            if "maladie" in demande.type_conge.lower():
                icon = "🏥"
                color = "🔴"
            elif "annuel" in demande.type_conge.lower() or "payé" in demande.type_conge.lower():
                icon = "🏖️"
                color = "🟢"
            elif "rtt" in demande.type_conge.lower():
                icon = "⚡"
                color = "🟡"
            elif "exceptionnel" in demande.type_conge.lower():
                icon = "🎯"
                color = "🟠"
            else:
                icon = "📄"
                color = "🔵"
            
            # Déterminer le statut
            statut = getattr(demande, 'status', getattr(demande, 'statut', 'en attente'))
            if statut.lower() in ['approuvé', 'validé', 'accepté']:
                statut_icon = "✅"
                statut_text = "APPROUVÉ"
            elif statut.lower() in ['rejeté', 'refusé']:
                statut_icon = "❌"
                statut_text = "REJETÉ"
            else:
                statut_icon = "⏳"
                statut_text = "EN ATTENTE"
            
            response += f"{color} {icon}  𝗗𝗘𝗠𝗔𝗡𝗗𝗘 #{i:02d}\n"
            response += f"    📝 𝗧𝘆𝗽𝗲 : {demande.type_conge.upper()}\n"
            response += f"    📅 𝗣𝗲́𝗿𝗶𝗼𝗱𝗲 : {demande.date_debut.strftime('%d/%m/%Y') if demande.date_debut else 'N/A'} → {demande.date_fin.strftime('%d/%m/%Y') if demande.date_fin else 'N/A'}\n"
            
            # Calculer la durée
            if demande.date_debut and demande.date_fin:
                duree = (demande.date_fin - demande.date_debut).days + 1
                response += f"    ⏱️ 𝗗𝘂𝗿𝗲́𝗲 : {duree} jour(s)\n"
            
            response += f"    💬 𝗥𝗮𝗶𝘀𝗼𝗻 : {demande.raison if demande.raison else 'Non spécifiée'}\n"
            response += f"    {statut_icon} 𝗦𝘁𝗮𝘁𝘂𝘁 : {statut_text}\n"
            response += f"    📋 𝗝𝘂𝘀𝘁𝗶𝗳𝗶𝗰𝗮𝘁𝗶𝗳 : {'✅ Fourni' if demande.preuve else '❌ Manquant'}\n"
            response += f"    📆 𝗦𝗼𝘂𝗺𝗶𝘀𝗲 : {demande.created_at.strftime('%d/%m/%Y %H:%M') if demande.created_at else 'N/A'}\n"
            response += "    ─────────────────────────────────────\n\n"
        
        response += "═══════════════════════════════════════════════════\n\n"
        
        # Statistiques rapides
        en_attente = sum(1 for d in mes_demandes if getattr(d, 'status', getattr(d, 'statut', 'en attente')).lower() in ['en attente', 'en cours'])
        approuvees = sum(1 for d in mes_demandes if getattr(d, 'status', getattr(d, 'statut', '')).lower() in ['approuvé', 'validé', 'accepté'])
        
        response += f"📊 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗾𝘂𝗲𝘀 :\n"
        response += f"   • ⏳ En attente : {en_attente}\n"
        response += f"   • ✅ Approuvées : {approuvees}\n"
        response += f"   • 📈 Total : {len(mes_demandes)}\n\n"
        response += "💡 Tapez 'demande congé' pour créer une nouvelle demande"
        
        return JSONResponse(content={"response": response})
    
    # 🔥 NOUVELLE FONCTIONNALITÉ : Prévisions de charge de travail (RH uniquement)
    elif intent == "workload_forecast":
        if not has_permission(user, "HR") and not has_permission(user, "RH"):
            return JSONResponse(content={"response": "⛔ Accès réservé aux ressources humaines."})
        
        analyse = analyser_charge_travail(db)
        
        response = "📊 𝗔𝗡𝗔𝗟𝗬𝗦𝗘 𝗗𝗘 𝗖𝗛𝗔𝗥𝗚𝗘 𝗗𝗘 𝗧𝗥𝗔𝗩𝗔𝗜𝗟\n\n"
        response += "═══════════════════════════════════════════════════\n\n"
        
        # Statistiques globales
        stats = analyse["stats_globales"]
        response += f"📈 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗾𝘂𝗲𝘀 𝗚𝗹𝗼𝗯𝗮𝗹𝗲𝘀\n"
        response += f"    👥 Total employés : {stats['total_users']}\n"
        response += f"    ✅ Employés actifs : {stats['users_actifs']}\n"
        response += f"    🔄 Missions en cours : {stats['users_missions_en_cours']}\n"
        response += f"    📊 Taux d'activité : {stats['taux_activite']}%\n\n"
        
        # Analyse par département
        response += "🏢 𝗔𝗻𝗮𝗹𝘆𝘀𝗲 𝗽𝗮𝗿 𝗗𝗲́𝗽𝗮𝗿𝘁𝗲𝗺𝗲𝗻𝘁\n"
        for dept, data in analyse["departments"].items():
            taux_charge = round((data["en_cours"] / data["total"] * 100) if data["total"] > 0 else 0, 1)
            
            if taux_charge >= 80:
                status_icon = "🔴"
                status = "SURCHARGE"
            elif taux_charge >= 60:
                status_icon = "🟡"
                status = "CHARGE ÉLEVÉE"
            else:
                status_icon = "🟢"
                status = "NORMALE"
                
            response += f"    {status_icon} {dept} : {taux_charge}% ({status})\n"
            response += f"        👥 {data['total']} employés | 🔄 {data['en_cours']} en mission\n"
            
            if data["missions"]:
                top_missions = list(set(data["missions"]))[:3]
                response += f"        📋 Missions fréquentes : {', '.join(top_missions)}\n"
            response += "\n"
        
        # Alertes de surcharge
        if analyse["users_surcharges"]:
            response += "🚨 𝗔𝗹𝗲𝗿𝘁𝗲𝘀 𝗦𝘂𝗿𝗰𝗵𝗮𝗿𝗴𝗲\n"
            for user_surcharge in analyse["users_surcharges"]:
                response += f"    ⚠️ {user_surcharge['nom']} ({user_surcharge['department']})\n"
                response += f"        🔢 {user_surcharge['nb_missions']} missions actives\n"
        else:
            response += "✅ 𝗔𝘂𝗰𝘂𝗻𝗲 𝘀𝘂𝗿𝗰𝗵𝗮𝗿𝗴𝗲 𝗱𝗲́𝘁𝗲𝗰𝘁𝗲́𝗲\n"
        
        response += "\n═══════════════════════════════════════════════════\n"
        response += "💡 𝗥𝗲𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝗮𝘁𝗶𝗼𝗻𝘀 :\n"
        
        if stats["taux_activite"] > 85:
            response += "   • 🔥 Forte activité détectée - Envisager du renfort\n"
        if analyse["users_surcharges"]:
            response += "   • ⚖️ Redistribuer les missions des employés surchargés\n"
            response += "   • 📞 Contact direct recommandé avec les équipes\n"
        
        response += "   • 📊 Tapez 'explication surcharge' pour plus de détails"
        
        return JSONResponse(content={"response": response})
    
    # 🔥 NOUVELLE FONCTIONNALITÉ : Alertes et explications de surcharge (RH uniquement)
    elif intent == "overload_alert":
        if not has_permission(user, "HR") and not has_permission(user, "RH"):
            return JSONResponse(content={"response": "⛔ Accès réservé aux ressources humaines."})
        
        analyse = analyser_charge_travail(db)
        users_surcharges = analyse["users_surcharges"]
        
        if not users_surcharges:
            return JSONResponse(content={
                "response": "✅ 𝗔𝘂𝗰𝘂𝗻𝗲 𝘀𝘂𝗿𝗰𝗵𝗮𝗿𝗴𝗲 𝗮𝗰𝘁𝘂𝗲𝗹𝗹𝗲\n\n" +
                           "Tous les employés ont une charge de travail normale (≤ 3 missions actives).\n\n" +
                           "📊 Tapez 'prévision charge' pour voir l'analyse complète."
            })
        
        response = "🚨 𝗘𝗫𝗣𝗟𝗜𝗖𝗔𝗧𝗜𝗢𝗡 𝗦𝗨𝗥𝗖𝗛𝗔𝗥𝗚𝗘 𝗘́𝗤𝗨𝗜𝗣𝗘\n\n"
        response += "═══════════════════════════════════════════════════\n\n"
        
        response += f"⚠️ {len(users_surcharges)} employé(s) en situation de surcharge détecté(s)\n\n"
        
        for i, user_surcharge in enumerate(users_surcharges, 1):
            response += f"📋 𝗘𝗺𝗽𝗹𝗼𝘆𝗲́ #{i}\n"
            response += f"    👤 𝗡𝗼𝗺 : {user_surcharge['nom']}\n"
            response += f"    🏢 𝗗𝗲́𝗽𝗮𝗿𝘁𝗲𝗺𝗲𝗻𝘁 : {user_surcharge['department']}\n"
            response += f"    🔢 𝗡𝗼𝗺𝗯𝗿𝗲 𝗱𝗲 𝗺𝗶𝘀𝘀𝗶𝗼𝗻𝘀 : {user_surcharge['nb_missions']}\n"
            response += f"    📝 𝗠𝗶𝘀𝘀𝗶𝗼𝗻𝘀 :\n"
            
            for mission in user_surcharge['missions']:
                response += f"        • {mission}\n"
            
            # Niveau de risque
            if user_surcharge['nb_missions'] >= 6:
                niveau = "🔴 CRITIQUE"
                action = "Action immédiate requise"
            elif user_surcharge['nb_missions'] >= 5:
                niveau = "🟠 ÉLEVÉ"
                action = "Surveillance rapprochée"
            else:
                niveau = "🟡 MODÉRÉ"
                action = "Rééquilibrage recommandé"
                
            response += f"    📊 𝗡𝗶𝘃𝗲𝗮𝘂 𝗱𝗲 𝗿𝗶𝘀𝗾𝘂𝗲 : {niveau}\n"
            response += f"    🎯 𝗔𝗰𝘁𝗶𝗼𝗻 : {action}\n\n"
        
        response += "═══════════════════════════════════════════════════\n\n"
        response += "🎯 𝗔𝗰𝘁𝗶𝗼𝗻𝘀 𝗿𝗲𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝗲́𝗲𝘀 :\n"
        response += "   • 📞 Contacter les employés surchargés\n"
        response += "   • ⚖️ Redistribuer les missions moins urgentes\n"
        response += "   • 👥 Envisager du renfort temporaire\n"
        response += "   • 📅 Planifier des congés échelonnés\n"
        response += "   • 🔄 Déléguer certaines tâches\n\n"
        response += "💡 Ces alertes sont automatiquement générées pour tout employé ayant plus de 3 missions actives."
        
        return JSONResponse(content={"response": response})
    
    # 🔥 NOUVELLE FONCTIONNALITÉ : Génération de rapport détaillé sur les congés (RH uniquement)
    elif intent == "generate_leave_report":
        if not has_permission(user, "HR") and not has_permission(user, "RH"):
            return JSONResponse(content={"response": "⛔ Accès réservé aux ressources humaines."})
        
        # Générer le rapport
        rapport_data = generer_rapport_conges(db)
        
        # Sauvegarder le rapport
        filename, file_path = sauvegarder_rapport(rapport_data, "conges", user.id)
        
        if not filename:
            return JSONResponse(content={"response": "❌ Erreur lors de la génération du rapport. Veuillez réessayer."})
        
        response = "📊 𝗥𝗔𝗣𝗣𝗢𝗥𝗧 𝗗'𝗔𝗡𝗔𝗟𝗬𝗦𝗘 𝗗𝗘𝗦 𝗖𝗢𝗡𝗚𝗘́𝗦 𝗚𝗘́𝗡𝗘́𝗥𝗘́\n\n"
        response += "═══════════════════════════════════════════════════\n\n"
        
        # Aperçu du rapport
        stats = rapport_data["statistiques_globales"]
        response += f"📈 𝗔𝗽𝗲𝗿𝗰̧𝘂 𝗱𝘂 𝗿𝗮𝗽𝗽𝗼𝗿𝘁 :\n"
        response += f"    📊 Total demandes analysées : {stats['total_demandes']}\n"
        response += f"    ✅ Taux de validation : {stats['taux_validation']}%\n"
        response += f"    📅 Durée moyenne : {stats['duree_moyenne']} jours\n"
        response += f"    📄 Avec justificatif : {stats['avec_justificatif']}\n"
        response += f"    🏢 Département le plus actif : {stats['departement_plus_actif']}\n\n"
        
        # Top 3 types de congés
        response += "🔝 𝗧𝗼𝗽 𝗧𝘆𝗽𝗲𝘀 𝗱𝗲 𝗖𝗼𝗻𝗴𝗲́𝘀 :\n"
        sorted_types = sorted(rapport_data["analyse_par_type"].items(), key=lambda x: x[1], reverse=True)[:3]
        for i, (type_conge, count) in enumerate(sorted_types, 1):
            pourcentage = round((count / stats['total_demandes'] * 100), 1)
            response += f"    {i}. {type_conge} : {count} ({pourcentage}%)\n"
        
        if rapport_data["recommandations"]:
            response += f"\n⚠️ 𝗥𝗲𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝗮𝘁𝗶𝗼𝗻𝘀 𝗖𝗹𝗲́𝘀 :\n"
            for rec in rapport_data["recommandations"][:2]:  # Top 2 recommandations
                response += f"    • {rec}\n"
        
        response += "\n═══════════════════════════════════════════════════\n\n"
        response += f"📁 𝗙𝗶𝗰𝗵𝗶𝗲𝗿 𝗴𝗲́𝗻𝗲́𝗿𝗲́ : {filename}\n"
        response += f"📥 𝗖𝗹𝗶𝗾𝘂𝗲𝘇 𝘀𝘂𝗿 𝗹𝗲 𝗯𝗼𝘂𝘁𝗼𝗻 𝗰𝗶-𝗱𝗲𝘀𝘀𝗼𝘂𝘀 𝗽𝗼𝘂𝗿 𝘁𝗲́𝗹𝗲́𝗰𝗵𝗮𝗿𝗴𝗲𝗿 𝗹𝗲 𝗿𝗮𝗽𝗽𝗼𝗿𝘁 𝗰𝗼𝗺𝗽𝗹𝗲𝘁\n\n"
        response += "💡 Le rapport complet contient l'analyse détaillée par département,\n"
        response += "    les tendances temporelles et toutes les recommandations."
        
        # URL de téléchargement
        download_url = f"http://localhost:8000/download-report/{filename}?matricule={user.matricule}"
        
        return JSONResponse(content={
            "response": response, 
            "report_file": filename,
            "download_url": download_url,
            "show_download_button": True,
            "report_type": "conges"
        })
    
    # 🔥 NOUVELLE FONCTIONNALITÉ : Génération de rapport détaillé sur la charge de travail (RH uniquement)
    elif intent == "generate_workload_report":
        if not has_permission(user, "HR") and not has_permission(user, "RH"):
            return JSONResponse(content={"response": "⛔ Accès réservé aux ressources humaines."})
        
        # Générer le rapport
        rapport_data = generer_rapport_charge_travail(db)
        
        # Sauvegarder le rapport
        filename, file_path = sauvegarder_rapport(rapport_data, "charge", user.id)
        
        if not filename:
            return JSONResponse(content={"response": "❌ Erreur lors de la génération du rapport. Veuillez réessayer."})
        
        response = "📊 𝗥𝗔𝗣𝗣𝗢𝗥𝗧 𝗗𝗘 𝗖𝗛𝗔𝗥𝗚𝗘 𝗗𝗘 𝗧𝗥𝗔𝗩𝗔𝗜𝗟 𝗚𝗘́𝗡𝗘́𝗥𝗘́\n\n"
        response += "═══════════════════════════════════════════════════\n\n"
        
        # Aperçu du rapport
        resume = rapport_data["resume_executif"]
        response += f"🎯 𝗔𝗽𝗲𝗿𝗰̧𝘂 𝗘𝘅𝗲́𝗰𝘂𝘁𝗶𝗳 :\n"
        response += f"    📊 Taux d'activité global : {resume['taux_activite_global']}\n"
        response += f"    👥 Employés actifs : {resume['employes_actifs']}\n"
        response += f"    🔄 Missions en cours : {resume['missions_en_cours']}\n"
        response += f"    📈 Niveau de charge : {resume['niveau_charge_moyen']}\n"
        response += f"    ⚠️ Employés surchargés : {resume['employes_surcharges']}\n\n"
        
        # Départements à risque
        dept_risque = [dept for dept, data in rapport_data["analyse_departementale"].items() 
                      if "CRITIQUE" in data["niveau_risque"] or "ÉLEVÉ" in data["niveau_risque"]]
        
        if dept_risque:
            response += "🚨 𝗗𝗲́𝗽𝗮𝗿𝘁𝗲𝗺𝗲𝗻𝘁𝘀 𝗮̀ 𝗥𝗶𝘀𝗾𝘂𝗲 :\n"
            for dept in dept_risque[:3]:  # Top 3
                data = rapport_data["analyse_departementale"][dept]
                response += f"    🔴 {dept} : {data['taux_charge']} ({data['niveau_risque']})\n"
        else:
            response += "✅ 𝗔𝘂𝗰𝘂𝗻 𝗱𝗲́𝗽𝗮𝗿𝘁𝗲𝗺𝗲𝗻𝘁 𝗮̀ 𝗿𝗶𝘀𝗾𝘂𝗲 𝗱𝗲́𝘁𝗲𝗰𝘁𝗲́\n"
        
        # Prédictions clés
        predictions = rapport_data["predictions"]
        response += f"\n🔮 𝗣𝗿𝗲́𝗱𝗶𝗰𝘁𝗶𝗼𝗻𝘀 :\n"
        response += f"    📈 Charge prévue : {predictions['charge_globale_prevue']}\n"
        response += f"    👨‍💼 Besoin recrutement : {predictions['besoin_recrutement']}\n"
        response += f"    🔥 Risque burnout : {predictions['risque_burnout']}\n"
        
        if rapport_data["alertes_critiques"]:
            response += f"\n🚨 𝗔𝗹𝗲𝗿𝘁𝗲𝘀 𝗖𝗿𝗶𝘁𝗶𝗾𝘂𝗲𝘀 : {len(rapport_data['alertes_critiques'])}\n"
        
        response += "\n═══════════════════════════════════════════════════\n\n"
        response += f"📁 𝗙𝗶𝗰𝗵𝗶𝗲𝗿 𝗴𝗲́𝗻𝗲́𝗿𝗲́ : {filename}\n"
        response += f"📥 𝗖𝗹𝗶𝗾𝘂𝗲𝘇 𝘀𝘂𝗿 𝗹𝗲 𝗯𝗼𝘂𝘁𝗼𝗻 𝗰𝗶-𝗱𝗲𝘀𝘀𝗼𝘂𝘀 𝗽𝗼𝘂𝗿 𝘁𝗲́𝗹𝗲́𝗰𝗵𝗮𝗿𝗴𝗲𝗿 𝗹𝗲 𝗿𝗮𝗽𝗽𝗼𝗿𝘁 𝗰𝗼𝗺𝗽𝗹𝗲𝘁\n\n"
        response += "💡 Le rapport complet contient l'analyse individuelle détaillée,\n"
        response += "    les recommandations stratégiques et toutes les prédictions."
        
        # URL de téléchargement
        download_url = f"http://localhost:8000/download-report/{filename}?matricule={user.matricule}"
        
        return JSONResponse(content={
            "response": response, 
            "report_file": filename,
            "download_url": download_url,
            "show_download_button": True,
            "report_type": "charge"
        })
    
    # 🔥 NOUVELLE FONCTIONNALITÉ : Gestion des téléchargements de rapports (RH uniquement)
    elif intent == "download_report":
        if not has_permission(user, "HR") and not has_permission(user, "RH"):
            return JSONResponse(content={"response": "⛔ Accès réservé aux ressources humaines."})
        
        # Extraire le nom du fichier à partir du message
        import re
        filename_match = re.search(r'(\w+_\d{8}_\d{6}\.txt)', message)
        if not filename_match:
            return JSONResponse(content={"response": "❌ Nom de fichier invalide. Utilisez le format: télécharger [nom_fichier.txt]"})
        
        filename = filename_match.group(1)
        
        # Vérifier que le fichier existe et appartient à l'utilisateur
        import os
        file_path = f"backend/app/reports/{filename}"
        if not os.path.exists(file_path):
            return JSONResponse(content={"response": "❌ Fichier introuvable. Le rapport a peut-être expiré."})
        
        # Vérifier que le fichier appartient bien à l'utilisateur (format: type_userID_date.txt)
        if not filename.split('_')[1] == str(user.id):
            return JSONResponse(content={"response": "⛔ Vous ne pouvez télécharger que vos propres rapports."})
        
        download_url = f"http://localhost:8000/download-report/{filename}?matricule={user.matricule}"
        
        response = f"📥 𝗧𝗘́𝗟𝗘́𝗖𝗛𝗔𝗥𝗚𝗘𝗠𝗘𝗡𝗧 𝗗𝗨 𝗥𝗔𝗣𝗣𝗢𝗥𝗧\n\n"
        response += f"📁 Fichier : {filename}\n"
        response += f"🔗 Cliquez sur le bouton ci-dessous pour télécharger\n\n"
        response += "💡 Le téléchargement démarrera automatiquement."
        
        return JSONResponse(content={
            "response": response, 
            "download_url": download_url,
            "filename": filename
        })
    
    # Vérification des différentes demandes spécifiques
    if "email" in message or "adresse mail" in message:
        return JSONResponse(content={"response": f"Votre email est : {user.email}"})
    elif "prénom" in message or "first name" in message:
        return JSONResponse(content={"response": f"Votre prénom est : {user.first_name}"})
    elif "nom" in message or "last name" in message:
        return JSONResponse(content={"response": f"Votre nom est : {user.last_name}"})
    elif "mon rôle" in message or "mon role" in message:
        return JSONResponse(content={"response": f"Votre rôle est : {user.role}"})
    elif "mon department" in message or "mon departement" in message:
        return JSONResponse(content={"response": f"Votre department est : {user.department}"})
    elif "date de mise à jour" in message or "updated at" in message:
        return JSONResponse(content={"response": f"Votre dernier update est : {user.updated_at}"})
    elif "solde de congés" in message or "solde congé" in message or "solde de conges" in message or "solde conges" in message or "solde_conges" in message or "combien de congés" in message or "combien de jours de congé" in message or "mon solde de congé" in message or "mes congés restants" in message:
        return JSONResponse(content={"response": f"Votre solde de congés payés est : {user.solde_conges if user.solde_conges is not None else 'Non renseigné'} jours."})
    elif "solde rtt" in message or "solde de rtt" in message or "combien de rtt" in message or "mes rtt" in message or "mon solde rtt" in message or "solde_rtt" in message:
        return JSONResponse(content={"response": f"Votre solde de RTT est : {user.solde_rtt if user.solde_rtt is not None else 'Non renseigné'} jours."})
    elif "mon statut" in message or "statut d'employé" in message or "statut_employe" in message or "mon statut" in message or "type de contrat" in message or "cdi" in message or "cdd" in message or "stagiaire" in message or "alternant" in message or "quel est mon statut" in message:
        return JSONResponse(content={"response": f"Votre statut d'employé est : {user.statut_employe if user.statut_employe else 'Non renseigné'}"})
    elif "date dernier congé" in message or "dernier congé" in message or "date_dernier_conge" in message or "quand mon dernier congé" in message or "date de mon dernier congé" in message:
        return JSONResponse(content={"response": f"La date de votre dernier congé est : {user.date_dernier_conge if user.date_dernier_conge else 'Non renseignée'}"})
    elif "date maj solde" in message or "date mise à jour solde" in message or "date_maj_solde" in message or "quand solde mis à jour" in message or "date de mise à jour du solde" in message:
        return JSONResponse(content={"response": f"La date de mise à jour de votre solde est : {user.date_maj_solde if user.date_maj_solde else 'Non renseignée'}"})


    # Vérification des permissions pour les demandes sensibles
    if "informations de l'utilisateur" in message or "informations de l'user" in message or "info user" in message:
        if not has_permission(user, "HR") and not has_permission(user, "RH"):
            return JSONResponse(content={"response": "Désolé, vous n'avez pas l'accès."})

        # Extraire le prénom et le nom de l'utilisateur cible
        first_name, last_name = extract_first_and_last_name(message)
        if not first_name or not last_name:
            return JSONResponse(content={"response": "Fournissez le prénom en premier, puis le nom de l'utilisateur."})

        # Rechercher l'utilisateur cible
        target_user = get_user_by_name(db, first_name, last_name)
        if not target_user:
            return JSONResponse(content={"response": f"Aucun utilisateur trouvé avec le prénom '{first_name}' et le nom '{last_name}'. Fournissez le prénom en premier, puis le nom."})

        # Afficher les informations de l'utilisateur cible
        header = f"{'Champ':<20} {'Valeur':<40}"
        separator = '-' * 62
        rows = [
            f"{'Matricule':<20} {str(target_user.matricule):<40}",
            f"{'Prénom':<20} {target_user.first_name:<40}",
            f"{'Nom':<20} {target_user.last_name:<40}",
            f"{'Email':<20} {target_user.email:<40}",
            f"{'Rôle':<20} {target_user.role:<40}",
            f"{'Département':<20} {target_user.department:<40}",
            f"{'Date création':<20} {str(target_user.created_at):<40}",
            f"{'Dernière maj':<20} {str(target_user.updated_at):<40}"
        ]
        tableau = f"\n{header}\n{separator}\n" + "\n".join(rows)
        legende = "\n\nLégende :\n- Champ : information\n- Valeur : donnée correspondante de l'utilisateur"
        return JSONResponse(content={"response": f"Informations de l'utilisateur {target_user.first_name} {target_user.last_name} :" + tableau + legende})

    # Extraire les mots-clés du message
    keywords = message.split()
    logger.debug(f"Mots-clés extraits : {keywords}")

    # Vérifier si les mots-clés correspondent à un titre d'instruction
    instruction = get_instruction_by_keywords(db, keywords)
    if instruction:
        response_message = instruction.description
        response_message += f"\n\nEst-ce que vous voulez que je le fasse pour vous ? Répondez par 'oui' ou 'non'."
        # Enregistrer l'état de la conversation pour attendre une réponse "oui" ou "non"
        chat_log = create_chat_log(user.id, f"{instruction.title}\n{response_message}")
        db.add(chat_log)
        db.commit()
        return JSONResponse(content={"response": response_message})

    # Log du message utilisateur
    chat_log = create_chat_log(user.id, request.message, "user")
    db.add(chat_log)
    db.commit()    # Au lieu d'utiliser GPT-2 qui génère n'importe quoi, retourner une réponse intelligente
    # Vérifier s'il s'agit d'une question générale
    if any(word in message.lower() for word in ["aide", "help", "que", "comment", "pourquoi", "quoi", "?"]):
        if has_permission(user, "HR") or has_permission(user, "RH"):
            # Menu d'aide spécialisé pour les RH
            return JSONResponse(content={
                "response": "🎯 𝗙𝗼𝗻𝗰𝘁𝗶𝗼𝗻𝗻𝗮𝗹𝗶𝘁𝗲́𝘀 𝗱𝗶𝘀𝗽𝗼𝗻𝗶𝗯𝗹𝗲𝘀 (𝗥𝗛) :\n\n" +
                           "📊 𝗚𝗲𝘀𝘁𝗶𝗼𝗻 𝗱𝗲𝘀 𝗖𝗼𝗻𝗴𝗲́𝘀 :\n" +
                           "• Tapez 'liste de congé' pour voir toutes les demandes\n" +
                           "• Tapez 'procedure congé' pour les procédures\n\n" +
                           "📈 𝗔𝗻𝗮𝗹𝘆𝘀𝗲 𝗱𝗲 𝗖𝗵𝗮𝗿𝗴𝗲 :\n" +
                           "• Tapez 'prévision charge' pour l'analyse complète\n" +
                           "• Tapez 'charge de travail' pour les statistiques\n\n" +
                           "🚨 𝗔𝗹𝗲𝗿𝘁𝗲𝘀 :\n" +
                           "• Tapez 'surcharge équipe' pour les alertes\n" +
                           "• Tapez 'explication surcharge' pour les détails\n\n" +
                           "ℹ️ 𝗔𝘂𝘁𝗿𝗲𝘀 :\n" +
                           "• Informations personnelles et historique\n" +
                           "• Gestion des notifications\n\n" +
                           "Que souhaitez-vous consulter ?"
            })
        else:
            # Menu d'aide standard pour les employés
            return JSONResponse(content={
                "response": "Je peux vous aider avec :\n" +
                           "- Vos informations personnelles (email, nom, prénom, etc.)\n" +
                           "- Vos demandes de congé\n" +
                           "- Votre solde de congés et RTT\n" +
                           "- L'historique de vos demandes\n" +
                           "- Les procédures de congé\n\n" +
                           "Que souhaitez-vous savoir ?"
            })
    
    # Si aucune intention n'est détectée, réponse par défaut
    return JSONResponse(content={
        "response": "Je n'ai pas bien compris votre demande. Pouvez-vous reformuler ou demander de l'aide pour voir ce que je peux faire pour vous ?"
    })

@app.post("/upload-proof/")
async def upload_proof(
    matricule: str = Form(...),
    proof: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_user_by_matricule(db, matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    # Vérifier qu'il y a une demande de congé en attente dans temp_memory
    if user.id not in temp_memory or temp_memory[user.id]["step"] != "upload_proof":
        # Correction : si la raison n'est pas encore mémorisée, la stocker et passer à l'étape upload_proof
        if user.id in temp_memory and temp_memory[user.id]["step"] == "collect_reason":
            temp_memory[user.id]["data"]["raison"] = "(preuve uploadée sans raison explicite)"
            temp_memory[user.id]["step"] = "upload_proof"
        else:
            raise HTTPException(status_code=400, detail="Aucune demande de congé en attente de preuve.")
    data = temp_memory[user.id]["data"]
    # Enregistrer le fichier preuve de façon robuste
    uploads_dir = "backend/app/uploads"
    import os
    os.makedirs(uploads_dir, exist_ok=True)
    file_ext = os.path.splitext(proof.filename)[1] if proof.filename else ''
    filename = f"preuve_{user.id}_{int(datetime.now().timestamp())}{file_ext}"
    file_path = os.path.join(uploads_dir, filename)
    with open(file_path, "wb") as f:
        content = await proof.read()
        f.write(content)
    # Enregistrer la demande de congé avec la preuve
    from app.models.demande_conge import DemandeConge
    demande = DemandeConge(
        user_id=user.id,
        type_conge=data["type_conge"],
        date_debut=datetime.strptime(data["date_debut"], "%Y-%m-%d"),
        date_fin=datetime.strptime(data["date_fin"], "%Y-%m-%d"),
        raison=data["raison"],
        preuve=file_path,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(demande)
    db.commit()
    
    # 🔥 NOTIFICATION AUTOMATIQUE AUX RH
    # Notifier tous les utilisateurs RH d'une nouvelle demande de congé
    users_rh = db.query(User).filter(User.department.in_(["RH", "HR"])).all()
    if users_rh:
        from app.models.notification import Notification
        notification_message = (
            f"📋 𝗡𝗼𝘂𝘃𝗲𝗹𝗹𝗲 𝗱𝗲𝗺𝗮𝗻𝗱𝗲 𝗱𝗲 𝗰𝗼𝗻𝗴𝗲́\n\n"
            f"👤 Employé : {user.first_name} {user.last_name}\n"
            f"📅 Type : {data['type_conge'].capitalize()}\n"
            f"🗓️ Période : {data['date_debut']} → {data['date_fin']}\n\n"
            f"💬 Tapez 'liste de congé' pour vérifier"
        )
        
        for user_rh in users_rh:
            notification = Notification(
                user_id=user_rh.id,
                title="Nouvelle demande de congé",
                message=notification_message,
                type="info",
                is_read=False,
                related_id=demande.id,
                created_at=datetime.utcnow()
            )
            db.add(notification)
        db.commit()
    
    # 🔥 VÉRIFICATION AUTOMATIQUE DE SURCHARGE
    # Analyser la charge de travail et notifier en cas de surcharge
    analyse = analyser_charge_travail(db)
    if analyse["users_surcharges"] and users_rh:
        creer_notification_surcharge(db, users_rh, analyse["users_surcharges"])
    # Mettre à jour le CSV utilisateur
    from app.models.demande_fichier import DemandeFichier
    user_file_entry = db.query(DemandeFichier).filter(DemandeFichier.user_id == user.id).first()
    csv_file_path = None
    if user_file_entry:
        csv_file_path = user_file_entry.fichier_csv
    else:
        generated_path = os.path.join("c:\\Users\\asus\\Desktop\\try\\backend\\app\\crud", f"demandes_conge_user_{user.id}.csv")
        new_file_entry = DemandeFichier(user_id=user.id, fichier_csv=generated_path)
        db.add(new_file_entry)
        db.commit()
        # Correction robuste : recharger l'entrée, sinon utiliser le chemin généré
        user_file_entry = db.query(DemandeFichier).filter(DemandeFichier.user_id == user.id).first()
        csv_file_path = user_file_entry.fichier_csv if user_file_entry and user_file_entry.fichier_csv else generated_path
    fieldnames = ["Type de Congé", "Date de Début", "Date de Fin", "Raison", "Preuve"]
    import csv
    try:
        file_exists = os.path.isfile(csv_file_path)
        with open(csv_file_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "Type de Congé": data["type_conge"].capitalize(),
                "Date de Début": data["date_debut"],
                "Date de Fin": data["date_fin"],
                "Raison": data["raison"].capitalize() if data["raison"] else "Non spécifiée",
                "Preuve": file_path
            })
    except Exception as e:
        logger.error(f"Erreur lors de l'écriture dans le fichier CSV : {e}")    # Nettoyer la mémoire temporaire seulement après succès complet
    if user.id in temp_memory:
        del temp_memory[user.id]

    # --- Calcul du pourcentage d'acceptation de congé ---
    status = user.status or ""
    current_missions = user.current_missions or ""
    missions_status = user.missions_status or ""
    manager = getattr(user, 'manager', None) if hasattr(user, 'manager') else None
    conseils = generer_conseils_personnalises(current_missions, manager)
    if status.lower() == "actif" and missions_status.lower() == "en pause":
        pourcentage = 90
        explication = (
            "Votre statut est actif et toutes vos missions sont actuellement en pause. "
            "Cela signifie que vous n'avez pas de tâches urgentes en attente, ce qui augmente fortement vos chances d'obtenir un congé. "
            f"{conseils}"
        )
    elif status.lower() == "actif" and missions_status.lower() == "en cours":
        pourcentage = 60
        explication = (
            "Votre statut est actif et vous avez des missions en cours. "
            f"Missions en cours : {current_missions if current_missions else 'non spécifiées'}. "
            "Cela signifie que certaines de vos tâches ne sont pas encore terminées, ce qui peut réduire la probabilité d'acceptation de votre congé. "
            "Il est conseillé de finaliser ou de déléguer vos missions avant de faire une demande de congé pour augmenter vos chances. "
            f"{conseils}"
        )
    else:
        pourcentage = 30
        explication = (
            f"Votre statut actuel est : '{status if status else 'non spécifié'}' et l'état de vos missions est : '{missions_status if missions_status else 'non spécifié'}'. "
            f"Missions en cours : {current_missions if current_missions else 'non spécifiées'}. "
            "Dans cette situation, il est probable que vos missions ne soient pas terminées ou que votre statut ne soit pas optimal pour une demande de congé. "
            "Merci de vérifier l'état de vos missions ou de contacter votre responsable pour plus d'informations. "
            f"{conseils}"
        )
    # --- Mémorisation du dernier calcul pour explication interactive ---
    temp_memory[user.id] = temp_memory.get(user.id, {})
    temp_memory[user.id]["last_acceptance_calc"] = {
        "pourcentage": pourcentage,
        "explication": explication
    }
    return JSONResponse(content={
        "response": "Votre demande de congé a été enregistrée avec succès, avec le fichier justificatif.",
        "acceptance_percentage": pourcentage,
        "explanation": explication
    })

# Endpoints pour les notifications
@app.get("/notifications/{matricule}")
async def get_notifications(matricule: str, unread_only: bool = False, db: Session = Depends(get_db)):
    """Récupérer les notifications d'un utilisateur"""
    user = get_user_by_matricule(db, matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    
    notifications = get_user_notifications(db, user.id, unread_only)
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "type": notif.type,
            "is_read": notif.is_read,
            "related_id": notif.related_id,
            "created_at": notif.created_at.strftime('%Y-%m-%d %H:%M:%S') if notif.created_at else ""
        })
    
    return JSONResponse(content={"notifications": notifications_data})

@app.get("/notifications/{matricule}/count")
async def get_notifications_count(matricule: str, db: Session = Depends(get_db)):
    """Récupérer le nombre de notifications non lues"""
    user = get_user_by_matricule(db, matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    
    count = get_unread_count(db, user.id)
    return JSONResponse(content={"unread_count": count})

@app.post("/notifications/{matricule}/{notification_id}/read")
async def mark_notification_read(matricule: str, notification_id: int, db: Session = Depends(get_db)):
    """Marquer une notification comme lue"""
    user = get_user_by_matricule(db, matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    
    success = mark_notification_as_read(db, notification_id, user.id)
    if success:
        return JSONResponse(content={"success": True, "message": "Notification marquée comme lue."})
    else:
        raise HTTPException(status_code=404, detail="Notification non trouvée.")

@app.post("/notifications/{matricule}/read-all")
async def mark_all_notifications_read(matricule: str, db: Session = Depends(get_db)):
    """Marquer toutes les notifications comme lues"""
    user = get_user_by_matricule(db, matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    
    count = mark_all_notifications_as_read(db, user.id)
    return JSONResponse(content={"success": True, "message": f"{count} notifications marquées comme lues."})

# Fonction pour générer des conseils personnalisés selon les missions
def generer_conseils_personnalises(current_missions, manager=None):
    conseils = []
    # Suggestions sur la délégation
    if current_missions:
        missions = [m.strip() for m in current_missions.split(',') if m.strip()]
        for mission in missions:
            conseils.append(f"Vous pouvez déléguer la mission '{mission}' à un collègue de confiance.")
    # Suggestion de prévenir le manager
    if manager:
        conseils.append(f"Pensez à prévenir votre manager ({manager}) de votre demande de congé.")
    else:
        conseils.append("Pensez à prévenir votre manager de votre demande de congé.")
    return ' '.join(conseils)

# Fonction pour analyser la charge de travail de l'équipe
def analyser_charge_travail(db: Session):
    users = db.query(User).all()
    
    # Statistiques globales
    total_users = len(users)
    users_actifs = len([u for u in users if u.status and u.status.lower() == "actif"])
    users_missions_en_cours = len([u for u in users if u.missions_status and u.missions_status.lower() == "en cours"])
    
    # Analyse par département
    departments = {}
    users_surcharges = []
    
    for user in users:
        dept = user.department or "Non défini"
        if dept not in departments:
            departments[dept] = {
                "total": 0,
                "actifs": 0,
                "en_cours": 0,
                "missions": []
            }
        
        departments[dept]["total"] += 1
        if user.status and user.status.lower() == "actif":
            departments[dept]["actifs"] += 1
        if user.missions_status and user.missions_status.lower() == "en cours":
            departments[dept]["en_cours"] += 1
            
        # Analyser les missions individuelles
        if user.current_missions:
            missions = [m.strip() for m in user.current_missions.split(',') if m.strip()]
            departments[dept]["missions"].extend(missions)
            
            # Détecter la surcharge (plus de 3 missions en cours)
            if len(missions) > 3 and user.missions_status and user.missions_status.lower() == "en cours":
                users_surcharges.append({
                    "nom": f"{user.first_name} {user.last_name}",
                    "department": dept,
                    "nb_missions": len(missions),
                    "missions": missions
                })
    
    return {
        "stats_globales": {
            "total_users": total_users,
            "users_actifs": users_actifs,
            "users_missions_en_cours": users_missions_en_cours,
            "taux_activite": round((users_actifs / total_users * 100) if total_users > 0 else 0, 1)
        },
        "departments": departments,
        "users_surcharges": users_surcharges
    }

# Fonction pour créer une notification de surcharge
def creer_notification_surcharge(db: Session, users_rh: list, users_surcharges: list):
    from app.models.notification import Notification
    
    if not users_surcharges:
        return
        
    message = f"🚨 𝗔𝗹𝗲𝗿𝘁𝗲 𝗦𝘂𝗿𝗰𝗵𝗮𝗿𝗴𝗲 𝗗𝗲́𝘁𝗲𝗰𝘁𝗲́𝗲\n\n"
    message += f"{len(users_surcharges)} employé(s) en surcharge détecté(s):\n\n"
    
    for user_surcharge in users_surcharges:
        message += f"• {user_surcharge['nom']} ({user_surcharge['department']}) - {user_surcharge['nb_missions']} missions\n"
    
    message += f"\n💬 Tapez 'explication surcharge' pour plus de détails"
    
    for user_rh in users_rh:
        notification = Notification(
            user_id=user_rh.id,
            title="Alerte Surcharge Équipe",
            message=message,
            type="warning",
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notification)
    
    db.commit()

# Fonction pour générer un rapport détaillé sur les demandes de congés
def generer_rapport_conges(db: Session):
    from app.models.demande_conge import DemandeConge
    from app.models.user import User as UserModel
    
    # Récupérer toutes les demandes avec les informations utilisateur
    demandes = db.query(DemandeConge).order_by(DemandeConge.created_at.desc()).all()
    
    rapport = {
        "metadata": {
            "titre": "RAPPORT D'ANALYSE DÉTAILLÉ - DEMANDES DE CONGÉS",
            "date_generation": datetime.now().strftime("%d/%m/%Y à %H:%M"),
            "periode_analyse": "Données complètes",
            "total_demandes": len(demandes)
        },
        "statistiques_globales": {},
        "analyse_par_type": {},
        "analyse_par_departement": {},
        "analyse_temporelle": {},
        "demandes_detaillees": [],
        "recommandations": []
    }
    
    if not demandes:
        return rapport
    
    # Statistiques globales
    types_conges = {}
    departements = {}
    statuts = {}
    mois_demandes = {}
    
    for demande in demandes:
        # Récupérer l'utilisateur
        utilisateur = db.query(UserModel).filter(UserModel.id == demande.user_id).first()
        
        # Analyse par type
        type_conge = demande.type_conge or "Non spécifié"
        types_conges[type_conge] = types_conges.get(type_conge, 0) + 1
        
        # Analyse par département
        dept = utilisateur.department if utilisateur else "Non défini"
        departements[dept] = departements.get(dept, 0) + 1
        
        # Analyse par statut
        statut = getattr(demande, 'status', getattr(demande, 'statut', 'en attente'))
        statuts[statut] = statuts.get(statut, 0) + 1
        
        # Analyse temporelle
        if demande.created_at:
            mois = demande.created_at.strftime("%Y-%m")
            mois_demandes[mois] = mois_demandes.get(mois, 0) + 1
        
        # Détails de la demande
        rapport["demandes_detaillees"].append({
            "id": demande.id,
            "employe": f"{utilisateur.first_name} {utilisateur.last_name}" if utilisateur else "Inconnu",
            "matricule": utilisateur.matricule if utilisateur else "N/A",
            "department": dept,
            "type_conge": type_conge,
            "date_debut": demande.date_debut.strftime('%d/%m/%Y') if demande.date_debut else "N/A",
            "date_fin": demande.date_fin.strftime('%d/%m/%Y') if demande.date_fin else "N/A",
            "duree_jours": (demande.date_fin - demande.date_debut).days + 1 if demande.date_debut and demande.date_fin else 0,
            "raison": demande.raison or "Non spécifiée",
            "statut": statut,
            "date_demande": demande.created_at.strftime('%d/%m/%Y %H:%M') if demande.created_at else "N/A",
            "preuve_fournie": "Oui" if demande.preuve else "Non"
        })
    
    # Remplir les statistiques
    rapport["statistiques_globales"] = {
        "total_demandes": len(demandes),
        "taux_validation": round((statuts.get('approuvé', 0) / len(demandes) * 100), 1) if demandes else 0,
        "duree_moyenne": round(sum(d["duree_jours"] for d in rapport["demandes_detaillees"]) / len(demandes), 1) if demandes else 0,
        "avec_justificatif": sum(1 for d in rapport["demandes_detaillees"] if d["preuve_fournie"] == "Oui"),
        "departement_plus_actif": max(departements.items(), key=lambda x: x[1])[0] if departements else "N/A"
    }
    
    rapport["analyse_par_type"] = types_conges
    rapport["analyse_par_departement"] = departements
    rapport["analyse_temporelle"] = dict(sorted(mois_demandes.items()))
    
    # Recommandations basées sur l'analyse
    recommandations = []
    
    if statuts.get('en attente', 0) > len(demandes) * 0.3:
        recommandations.append("Traitement des demandes en attente à prioriser (>30% en attente)")
    
    if types_conges.get('maladie', 0) > len(demandes) * 0.4:
        recommandations.append("Taux élevé de congés maladie détecté - Enquête de bien-être recommandée")
    
    if rapport["statistiques_globales"]["duree_moyenne"] > 7:
        recommandations.append("Durée moyenne des congés élevée - Vérifier la planification")
    
    if len(departements) > 0:
        dept_max = max(departements.values())
        if dept_max > len(demandes) * 0.5:
            recommandations.append("Concentration des demandes dans un département - Redistribution à considérer")
    
    rapport["recommandations"] = recommandations
    
    return rapport

# Fonction pour générer un rapport détaillé sur la charge de travail
def generer_rapport_charge_travail(db: Session):
    analyse = analyser_charge_travail(db)
    users = db.query(User).all()
    
    rapport = {
        "metadata": {
            "titre": "RAPPORT D'ANALYSE DÉTAILLÉ - PRÉVISION DE CHARGE DE TRAVAIL",
            "date_generation": datetime.now().strftime("%d/%m/%Y à %H:%M"),
            "periode_analyse": "État actuel",
            "total_employes": len(users)
        },
        "resume_executif": {},
        "analyse_departementale": {},
        "analyse_individuelle": [],
        "predictions": {},
        "alertes_critiques": [],
        "recommandations_strategiques": []
    }
    
    # Résumé exécutif
    stats = analyse["stats_globales"]
    rapport["resume_executif"] = {
        "taux_activite_global": f"{stats['taux_activite']}%",
        "employes_actifs": f"{stats['users_actifs']}/{stats['total_users']}",
        "missions_en_cours": stats['users_missions_en_cours'],
        "niveau_charge_moyen": "Élevé" if stats['taux_activite'] > 80 else "Modéré" if stats['taux_activite'] > 60 else "Normal",
        "employes_surcharges": len(analyse["users_surcharges"]),
        "departements_analyses": len(analyse["departments"])
    }
    
    # Analyse départementale détaillée
    for dept, data in analyse["departments"].items():
        taux_charge = round((data["en_cours"] / data["total"] * 100) if data["total"] > 0 else 0, 1)
        
        niveau_risque = "CRITIQUE" if taux_charge >= 90 else "ÉLEVÉ" if taux_charge >= 75 else "MODÉRÉ" if taux_charge >= 50 else "FAIBLE"
        
        missions_uniques = list(set(data["missions"]))
        
        rapport["analyse_departementale"][dept] = {
            "total_employes": data["total"],
            "employes_actifs": data["actifs"],
            "missions_en_cours": data["en_cours"],
            "taux_charge": f"{taux_charge}%",
            "niveau_risque": niveau_risque,
            "missions_types": missions_uniques[:10],  # Top 10 missions
            "nb_missions_differentes": len(missions_uniques),
            "capacite_restante": f"{100 - taux_charge}%"
        }
    
    # Analyse individuelle
    for user in users:
        missions = []
        if user.current_missions:
            missions = [m.strip() for m in user.current_missions.split(',') if m.strip()]
        
        niveau_charge = "CRITIQUE" if len(missions) >= 6 else "ÉLEVÉ" if len(missions) >= 4 else "NORMAL"
        
        rapport["analyse_individuelle"].append({
            "nom_complet": f"{user.first_name} {user.last_name}",
            "matricule": user.matricule,
            "department": user.department or "Non défini",
            "statut": user.status or "Non défini",
            "nb_missions_actives": len(missions),
            "missions_status": user.missions_status or "Non défini",
            "niveau_charge": niveau_charge,
            "missions_detaillees": missions,
            "disponibilite": "Limitée" if len(missions) >= 4 else "Bonne" if len(missions) <= 2 else "Moyenne"
        })
    
    # Prédictions basées sur les tendances
    total_missions_actives = sum(len(emp["missions_detaillees"]) for emp in rapport["analyse_individuelle"])
    
    rapport["predictions"] = {
        "charge_globale_prevue": "Croissante" if stats['taux_activite'] > 75 else "Stable",
        "besoin_recrutement": "Urgent" if len(analyse["users_surcharges"]) > stats['total_users'] * 0.2 else "À prévoir" if len(analyse["users_surcharges"]) > 0 else "Non nécessaire",
        "risque_burnout": "Élevé" if len(analyse["users_surcharges"]) > 3 else "Modéré" if len(analyse["users_surcharges"]) > 0 else "Faible",
        "missions_moyenne_par_employe": round(total_missions_actives / len(users), 1) if users else 0,
        "departements_a_surveiller": [dept for dept, data in rapport["analyse_departementale"].items() if "CRITIQUE" in data["niveau_risque"] or "ÉLEVÉ" in data["niveau_risque"]]
    }
    
    # Alertes critiques
    alertes = []
    
    for user_surcharge in analyse["users_surcharges"]:
        if user_surcharge['nb_missions'] >= 6:
            alertes.append(f"URGENCE: {user_surcharge['nom']} ({user_surcharge['nb_missions']} missions) - Intervention immédiate requise")
        elif user_surcharge['nb_missions'] >= 5:
            alertes.append(f"ATTENTION: {user_surcharge['nom']} ({user_surcharge['nb_missions']} missions) - Surveillance nécessaire")
    
    for dept, data in rapport["analyse_departementale"].items():
        if data["niveau_risque"] == "CRITIQUE":
            alertes.append(f"DÉPARTEMENT CRITIQUE: {dept} ({data['taux_charge']} de charge)")
    
    rapport["alertes_critiques"] = alertes
    
    # Recommandations stratégiques
    recommandations = []
    
    if len(analyse["users_surcharges"]) > 0:
        recommandations.append("Redistribution urgente des missions pour les employés surchargés")
        recommandations.append("Mise en place d'un système de délégation formalisé")
    
    if stats['taux_activite'] > 85:
        recommandations.append("Recrutement ou renfort temporaire à envisager")
        recommandations.append("Révision des processus pour optimiser l'efficacité")
    
    if len(rapport["predictions"]["departements_a_surveiller"]) > 0:
        recommandations.append("Audit approfondi des départements à risque")
        recommandations.append("Formation en gestion du temps et priorisation")
    
    recommandations.append("Mise en place d'indicateurs de suivi hebdomadaires")
    recommandations.append("Planification proactive des congés pour équilibrer la charge")
    
    rapport["recommandations_strategiques"] = recommandations
    
    return rapport

# Fonction pour formater et sauvegarder un rapport en fichier texte
def sauvegarder_rapport(rapport_data: dict, type_rapport: str, user_id: int):
    import os
    
    # Créer le dossier des rapports s'il n'existe pas
    reports_dir = "backend/app/reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    # Générer un nom de fichier unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_{type_rapport}_{user_id}_{timestamp}.txt"
    file_path = os.path.join(reports_dir, filename)
    
    # Formater le contenu du rapport
    contenu = f"""
{'='*80}
{rapport_data['metadata']['titre']}
{'='*80}

📅 Date de génération : {rapport_data['metadata']['date_generation']}
📊 Période d'analyse : {rapport_data['metadata']['periode_analyse']}

"""
    
    if type_rapport == "conges":
        contenu += f"""
🔍 RÉSUMÉ EXÉCUTIF
{'─'*50}
• Total des demandes analysées : {rapport_data['metadata']['total_demandes']}
• Taux de validation : {rapport_data['statistiques_globales']['taux_validation']}%
• Durée moyenne des congés : {rapport_data['statistiques_globales']['duree_moyenne']} jours
• Demandes avec justificatif : {rapport_data['statistiques_globales']['avec_justificatif']}
• Département le plus actif : {rapport_data['statistiques_globales']['departement_plus_actif']}

📈 ANALYSE PAR TYPE DE CONGÉ
{'─'*50}
"""
        for type_conge, count in rapport_data['analyse_par_type'].items():
            pourcentage = round((count / rapport_data['metadata']['total_demandes'] * 100), 1)
            contenu += f"• {type_conge:20} : {count:3} demandes ({pourcentage:5.1f}%)\n"
        
        contenu += f"""
🏢 ANALYSE PAR DÉPARTEMENT
{'─'*50}
"""
        for dept, count in rapport_data['analyse_par_departement'].items():
            pourcentage = round((count / rapport_data['metadata']['total_demandes'] * 100), 1)
            contenu += f"• {dept:20} : {count:3} demandes ({pourcentage:5.1f}%)\n"
        
        if rapport_data['recommandations']:
            contenu += f"""
💡 RECOMMANDATIONS
{'─'*50}
"""
            for i, rec in enumerate(rapport_data['recommandations'], 1):
                contenu += f"{i}. {rec}\n"
    
    elif type_rapport == "charge":
        contenu += f"""
🎯 RÉSUMÉ EXÉCUTIF
{'─'*50}
• Taux d'activité global : {rapport_data['resume_executif']['taux_activite_global']}
• Employés actifs : {rapport_data['resume_executif']['employes_actifs']}
• Missions en cours : {rapport_data['resume_executif']['missions_en_cours']}
• Niveau de charge moyen : {rapport_data['resume_executif']['niveau_charge_moyen']}
• Employés en surcharge : {rapport_data['resume_executif']['employes_surcharges']}

🏢 ANALYSE DÉPARTEMENTALE
{'─'*50}
"""
        for dept, data in rapport_data['analyse_departementale'].items():
            contenu += f"""
Département : {dept}
• Employés : {data['employes_actifs']}/{data['total_employes']} actifs
• Taux de charge : {data['taux_charge']}
• Niveau de risque : {data['niveau_risque']}
• Types de missions : {len(data['missions_types'])} différentes
• Capacité restante : {data['capacite_restante']}
"""
        
        if rapport_data['alertes_critiques']:
            contenu += f"""
🚨 ALERTES CRITIQUES
{'─'*50}
"""
            for alerte in rapport_data['alertes_critiques']:
                contenu += f"⚠️ {alerte}\n"
        
        contenu += f"""
🔮 PRÉDICTIONS ET TENDANCES
{'─'*50}
• Charge globale prévue : {rapport_data['predictions']['charge_globale_prevue']}
• Besoin de recrutement : {rapport_data['predictions']['besoin_recrutement']}
• Risque de burnout : {rapport_data['predictions']['risque_burnout']}
• Missions moyenne/employé : {rapport_data['predictions']['missions_moyenne_par_employe']}

💡 RECOMMANDATIONS STRATÉGIQUES
{'─'*50}
"""
        for i, rec in enumerate(rapport_data['recommandations_strategiques'], 1):
            contenu += f"{i}. {rec}\n"
    
    contenu += f"""

{'='*80}
Rapport généré automatiquement par le Système de Gestion RH
Contact : Support RH pour toute question
{'='*80}
"""
    
    # Sauvegarder le fichier
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(contenu)
        return filename, file_path
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du rapport : {e}")
        return None, None

# Monter le routeur admin RH pour les endpoints /admin/demandes-conge
app.include_router(demande_conge_admin_router)

# Endpoint pour télécharger les rapports générés
@app.get("/download-report/{filename}")
async def download_report(filename: str, matricule: str, db: Session = Depends(get_db)):
    """Télécharger un rapport généré par le chatbot"""
    user = get_user_by_matricule(db, matricule)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    
    # Vérifier les permissions RH
    if not has_permission(user, "HR") and not has_permission(user, "RH"):
        raise HTTPException(status_code=403, detail="Accès réservé aux ressources humaines.")
    
    # Construire le chemin du fichier
    import os
    file_path = os.path.join("backend/app/reports", filename)
    
    # Vérifier que le fichier existe
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Fichier de rapport non trouvé.")
    
    # Vérifier que le fichier appartient à l'utilisateur (basé sur le nom du fichier)
    if f"_{user.id}_" not in filename:
        raise HTTPException(status_code=403, detail="Accès non autorisé à ce rapport.")
    
    from fastapi.responses import FileResponse
    
    # Retourner le fichier pour téléchargement
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/plain; charset=utf-8',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
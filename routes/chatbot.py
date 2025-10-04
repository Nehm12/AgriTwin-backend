from flask import Blueprint, request, jsonify
from models import ChatbotMessage
from db import db

chatbot_bp = Blueprint('chatbot_bp', __name__)

# Ajouter un message utilisateur + réponse générée (simulé pour l'instant)
@chatbot_bp.route('/', methods=['POST'])
def send_message():
    data = request.json
    user_id = data['user_id']
    message = data['message']

    # Pour le moment, réponse simulée
    response = f"Réponse du bot pour le message : {message}"

    msg = ChatbotMessage(
        user_id=user_id,
        message=message,
        response=response
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({
        "message": "Message envoyé au chatbot",
        "id": msg.id,
        "response": response
    })

# Récupérer tous les messages pour un utilisateur
@chatbot_bp.route('/<int:user_id>', methods=['GET'])
def get_messages(user_id):
    msgs = ChatbotMessage.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": m.id,
        "message": m.message,
        "response": m.response,
        "created_at": m.created_at
    } for m in msgs])

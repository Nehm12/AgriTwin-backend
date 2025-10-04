from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from db import db

user_bp = Blueprint('user_bp', __name__)

# Créer un utilisateur
@user_bp.route('/', methods=['POST'])
def create_user():
    data = request.json
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    user = User(
        lastname=data['lastname'],
        firstname=data.get('firstname'),
        email=data.get('email'),
        phone=data['phone'],
        password=hashed_password,
        language=data.get('language', 'fr')
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Utilisateur créé", "id": user.id})

# Connexion utilisateur
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(phone=data['phone']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"message": "Échec de l'authentification"}), 401
    return jsonify({
        "message": "Connexion réussie",
        "user": {
            "id": user.id,
            "lastname": user.lastname,
            "firstname": user.firstname,
            "email": user.email,
            "phone": user.phone,
            "language": user.language
        }
    })

# Lister tous les utilisateurs
@user_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "lastname": u.lastname,
        "firstname": u.firstname,
        "email": u.email,
        "phone": u.phone,
        "language": u.language
    } for u in users])

# Récupérer un utilisateur par id
@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    u = User.query.get_or_404(user_id)
    return jsonify({
        "id": u.id,
        "lastname": u.lastname,
        "firstname": u.firstname,
        "email": u.email,
        "phone": u.phone,
        "language": u.language
    })

# Mettre à jour un utilisateur
@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    u = User.query.get_or_404(user_id)
    data = request.json
    u.lastname = data.get('lastname', u.lastname)
    u.firstname = data.get('firstname', u.firstname)
    u.email = data.get('email', u.email)
    u.phone = data.get('phone', u.phone)
    u.language = data.get('language', u.language)
    if data.get('password'):
        u.password = generate_password_hash(data['password'], method='sha256')
    db.session.commit()
    return jsonify({"message": "Utilisateur mis à jour"})

# Supprimer un utilisateur
@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "Utilisateur supprimé"})

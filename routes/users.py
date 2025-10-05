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
@user_bp.route("/login", methods=['POST'])
def login():
    data = request.json
    
    # Debug: afficher les données reçues
    print("Données reçues:", data)
    
    # Vérifier si phone est fourni
    if not data.get('phone'):
        return jsonify({"message": "Numéro de téléphone requis"}), 400
        
    user = User.query.filter_by(phone=data['phone']).first()
    
    # Debug
    print("Utilisateur trouvé:", user)
    
    if not user:
        return jsonify({"message": "Numéro de téléphone incorrect"}), 401
        
    # Vérifier le mot de passe
    if not check_password_hash(user.password, data['password']):
        return jsonify({"message": "Mot de passe incorrect"}), 401
        
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

#Mettre à jour le mot de passe
@user_bp.route('/<int:user_id>/password', methods=['PUT'])
def update_password(user_id):
    u = User.query.get_or_404(user_id)
    data = request.json
    if not data.get('oldpassword') or not data.get('password'):
        return jsonify({"message": "Ancien et nouveau mot de passe requis"}), 400
    if not check_password_hash(u.password, data['oldpassword']):
        return jsonify({"message": "Ancien mot de passe incorrect"}), 401
    u.password = generate_password_hash(data['password'], method='sha256')
    db.session.commit()
    return jsonify({"message": "Mot de passe mis à jour"})
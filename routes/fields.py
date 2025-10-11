from flask import Blueprint, request, jsonify
from models import Field, Alert
from utils.notification_utils import create_alert
from db import db

field_bp = Blueprint('field_bp', __name__)

# Créer un champ
@field_bp.route('/', methods=['POST'])
def create_field():
    data = request.json
    field = Field(
        user_id=data['user_id'],
        name=data.get('name'),
        lat=data['lat'],
        lon=data['lon'],
        area=data.get('area'),
        country=data.get('country'),
        city=data.get('city'),
        crop_type_id=data.get('crop_type_id')
    )
    db.session.add(field)
    db.session.commit()

    # Créer une alerte après la création du champ
    try:
      create_alert(
          field_id=field.id,
          type="field_created",
          message=f"Nouveau champ créé: {field.name or 'Sans nom'} ({field.lat}, {field.lon})",
          channels=["in_app"]
      )
    except Exception:
      db.session.rollback()

    return jsonify({"message": "Champ créé", "id": field.id})

# Lister tous les champs
@field_bp.route('/', methods=['GET'])
def get_fields():
    fields = Field.query.all()
    return jsonify([{
        "id": f.id,
        "user_id": f.user_id,
        "name": f.name,
        "lat": f.lat,
        "lon": f.lon,
        "area": f.area,
        "country": f.country,
        "city": f.city,
        "crop_type_id": f.crop_type_id
    } for f in fields])

# Récupérer un champ par id
@field_bp.route('/<int:field_id>', methods=['GET'])
def get_field(field_id):
    f = Field.query.get_or_404(field_id)
    return jsonify({
        "id": f.id,
        "user_id": f.user_id,
        "name": f.name,
        "lat": f.lat,
        "lon": f.lon,
        "area": f.area,
        "country": f.country,
        "city": f.city,
        "crop_type_id": f.crop_type_id
    })

# Mettre à jour un champ
@field_bp.route('/<int:field_id>', methods=['PUT'])
def update_field(field_id):
    f = Field.query.get_or_404(field_id)
    data = request.json
    f.name = data.get('name', f.name)
    f.lat = data.get('lat', f.lat)
    f.lon = data.get('lon', f.lon)
    f.area = data.get('area', f.area)
    f.country = data.get('country', f.country)
    f.city = data.get('city', f.city)
    f.crop_type_id = data.get('crop_type_id', f.crop_type_id)
    db.session.commit()

    # Créer une alerte après la mise à jour du champ
    try:
      create_alert(
          field_id=f.id,
          type="field_updated",
          message=f"Champ mis à jour: {f.name or 'Sans nom'}",
          channels=["in_app"]
      )
    except Exception:
      db.session.rollback()

    return jsonify({"message": "Champ mis à jour"})

# Récupérer tous les champs d'un utilisateur
@field_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_fields(user_id):
    fields = Field.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": f.id,
        "user_id": f.user_id,
        "name": f.name,
        "lat": f.lat,
        "lon": f.lon,
        "area": f.area,
        "country": f.country,
        "city": f.city,
        "crop_type_id": f.crop_type_id
    } for f in fields])
    
    
# Supprimer un champ
@field_bp.route('/<int:field_id>', methods=['DELETE'])
def delete_field(field_id):
    f = Field.query.get_or_404(field_id)
    db.session.delete(f)
    db.session.commit()
    return jsonify({"message": "Champ supprimé"})

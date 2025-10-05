from flask import Blueprint, request, jsonify
from models import Field, CropType
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

# Récupérer les champs pour l'utilisateur connecté
@field_bp.route('/user/<int:user_id>', methods=['GET'])
def get_fields_by_user(user_id):
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
    return jsonify({"message": "Champ mis à jour"})

# Supprimer un champ
@field_bp.route('/<int:field_id>', methods=['DELETE'])
def delete_field(field_id):
    f = Field.query.get_or_404(field_id)
    db.session.delete(f)
    db.session.commit()
    return jsonify({"message": "Champ supprimé"})

# Route pour les types de culture
@field_bp.route('/crops', methods=['GET'])
def get_crops():
    crops = CropType.query.all()
    return jsonify([{
        "id": crop.id,
        "name": crop.name,
        "optimal_temp": crop.optimal_temp,
        "optimal_soil_moisture": crop.optimal_soil_moisture,
        "cycle_days": crop.cycle_days,
    } for crop in crops])
    
@field_bp.route("/fields", methods=["GET"])
def get_all_fields():
    """Retourne tous les champs"""
    fields = Field.query.all()
    return jsonify([{
        'id': field.id,
        'name': field.name,
        'crop_type': field.crop_type,
        'area': field.area,
        'lat': field.lat,
        'lon': field.lon
    } for field in fields])     
from flask import Blueprint, request, jsonify
from models import CropType
from db import db

crop_bp = Blueprint('crop_bp', __name__)

# Créer un champ
@crop_bp.route('/', methods=['POST'])
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
@crop_bp.route('/', methods=['GET'])
def get_crops():
    crops = CropType.query.all()
    return jsonify([{
        
        "id": c.id,
        "name": c.name,
        "optimal_temp": c.optimal_temp,
        "optimal_soil_moisture": c.optimal_soil_moisture,
        "cycle_days": c.cycle_days
    } for c in crops])
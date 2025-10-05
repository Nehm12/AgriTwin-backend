from flask import Blueprint, request, jsonify
from models import CropType
from db import db

crop_bp = Blueprint('crop_bp', __name__)



# Lister tous les crops
@crop_bp.route('/', methods=['GET'])
def get_crop():
    crops = CropType.query.all()
    return jsonify([{
        "id": f.id,
        "name": f.name,
        "optimal_temp": f.optimal_temp,
        "optimal_soil_moisture": f.optimal_soil_moisture,
        "cycle_days": f.cycle_days,
        
    } for f in crops])


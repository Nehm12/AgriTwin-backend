# routes/environment.py
from flask import Blueprint, jsonify, request
from models import EnvironmentalData, Field
from db import db
from utils.raster_utils import extract_value_from_tiff
from datetime import datetime
import os
import glob

environment_bp = Blueprint('environment', __name__)

# Dossier principal contenant tous les fichiers
DATA_DIR = "data"

# Mapping des mots-clés pour détecter le type de fichier
VARIABLE_KEYWORDS = {
    "temperature": ["temp", "temperature", "t2m"],
    "precipitation": ["prec", "precipitation", "rain", "rainfall"],
    "humidity": ["hum", "humidity", "rh"],
    "ndvi": ["ndvi", "vegetation"],
    "wind_speed": ["wind", "speed", "ws"]
}

def detect_variable_type(filename):
    """Détecte automatiquement le type de variable depuis le nom du fichier"""
    filename_lower = filename.lower()
    for var_type, keywords in VARIABLE_KEYWORDS.items():
        if any(keyword in filename_lower for keyword in keywords):
            return var_type
    return "unknown"

def scan_all_rasters():
    """Scanne tous les fichiers .tif dans le dossier data/"""
    raster_files = {}
    
    # Cherche récursivement tous les .tif
    tif_files = glob.glob(os.path.join(DATA_DIR, "**/*.tif"), recursive=True)
    
    for tif_path in tif_files:
        filename = os.path.basename(tif_path)
        var_type = detect_variable_type(filename)
        
        # Stocke par type de variable (garde le dernier si plusieurs)
        if var_type not in raster_files:
            raster_files[var_type] = []
        raster_files[var_type].append(tif_path)
    
    return raster_files

# --------------------
# READ : obtenir TOUTES les valeurs pour un champ
# --------------------
@environment_bp.route("/<int:field_id>", methods=["GET"])
def get_environment(field_id):
    field = Field.query.get(field_id)
    if not field:
        return jsonify({"error": "Champ non trouvé"}), 404

    # Scanne automatiquement tous les rasters
    all_rasters = scan_all_rasters()
    
    data = {}
    file_details = {}
    
    for var_type, file_list in all_rasters.items():
        if var_type == "unknown":
            continue
            
        # Prend le fichier le plus récent (optionnel)
        file_path = file_list[-1]  # ou file_list[0] pour le premier
        
        try:
            value = extract_value_from_tiff(file_path, field.lat, field.lon)
            data[var_type] = value
            file_details[var_type] = {
                "file": os.path.basename(file_path),
                "count": len(file_list)  # nombre de fichiers trouvés
            }
        except Exception as e:
            data[var_type] = None
            file_details[var_type] = {"error": str(e)}

    return jsonify({
        "field_id": field.id,
        "field_name": field.name,
        "coordinates": {"lat": field.lat, "lon": field.lon},
        "data": data,
        "files_used": file_details,
        "timestamp": datetime.utcnow().isoformat()
    })

# --------------------
# GET : Liste tous les fichiers raster disponibles
# --------------------
@environment_bp.route("/files", methods=["GET"])
def list_raster_files():
    """Endpoint pour voir tous les fichiers détectés"""
    all_rasters = scan_all_rasters()
    
    summary = {}
    for var_type, files in all_rasters.items():
        summary[var_type] = {
            "count": len(files),
            "files": [os.path.basename(f) for f in files]
        }
    
    return jsonify({
        "total_files": sum(len(files) for files in all_rasters.values()),
        "by_variable": summary
    })

# --------------------
# CREATE : ajouter manuellement une donnée environnementale
# --------------------
@environment_bp.route("/environment", methods=["POST"])
def create_environment_data():
    json_data = request.get_json()
    try:
        env = EnvironmentalData(
            field_id=json_data["field_id"],
            temperature=json_data.get("temperature"),
            precipitation=json_data.get("precipitation"),
            humidity=json_data.get("humidity"),
            ndvi=json_data.get("ndvi"),
            wind_speed=json_data.get("wind_speed")
        )
        db.session.add(env)
        db.session.commit()
        return jsonify({"message": "Donnée environnementale ajoutée", "id": env.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --------------------
# UPDATE : modifier une donnée existante
# --------------------
@environment_bp.route("/environment/<int:data_id>", methods=["PUT"])
def update_environment_data(data_id):
    env = EnvironmentalData.query.get(data_id)
    if not env:
        return jsonify({"error": "Donnée non trouvée"}), 404

    json_data = request.get_json()
    env.temperature = json_data.get("temperature", env.temperature)
    env.precipitation = json_data.get("precipitation", env.precipitation)
    env.humidity = json_data.get("humidity", env.humidity)
    env.ndvi = json_data.get("ndvi", env.ndvi)
    env.wind_speed = json_data.get("wind_speed", env.wind_speed)
    db.session.commit()

    return jsonify({"message": "Donnée environnementale mise à jour"})

# --------------------
# DELETE : supprimer une donnée
# --------------------
@environment_bp.route("/environment/<int:data_id>", methods=["DELETE"])
def delete_environment_data(data_id):
    env = EnvironmentalData.query.get(data_id)
    if not env:
        return jsonify({"error": "Donnée non trouvée"}), 404

    db.session.delete(env)
    db.session.commit()
    return jsonify({"message": "Donnée environnementale supprimée"})
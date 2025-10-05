# routes/environment.py
from flask import Blueprint, jsonify, request
from models import EnvironmentalData, Field
from db import db
from utils.raster_utils import extract_value_from_tiff
from datetime import datetime
import os
import glob

environment_bp = Blueprint('environment', __name__)

# Dossiers possibles pour les fichiers (ordre de priorité)
DATA_DIRS = ["data", "data_drive"]

# URL du dossier Google Drive (optionnel)
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1apS8SJKooJIp_fW3HBvsIXT2LoffqULh?usp=drive_link"
DRIVE_DOWNLOAD_ENABLED = False  # Mettre True pour activer le téléchargement auto

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

def download_from_drive():
    """Télécharge les fichiers depuis Google Drive si activé"""
    if not DRIVE_DOWNLOAD_ENABLED:
        return False
    
    try:
        import gdown
        output_dir = "data_drive"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"📥 Téléchargement depuis Google Drive vers {output_dir}/...")
        gdown.download_folder(url=DRIVE_FOLDER_URL, output=output_dir, quiet=False, use_cookies=False)
        print("✅ Téléchargement terminé")
        return True
    except ImportError:
        print("⚠️ gdown non installé. Installer avec: pip install gdown")
        return False
    except Exception as e:
        print(f"❌ Erreur téléchargement Drive: {e}")
        return False

def scan_all_rasters(force_download=False):
    """Scanne tous les fichiers .tif dans les dossiers locaux et/ou Drive"""
    raster_files = {}
    found_files = []
    
    # Télécharge depuis Drive si demandé
    if force_download:
        download_from_drive()
    
    # Vérifie chaque dossier dans l'ordre de priorité
    for data_dir in DATA_DIRS:
        if os.path.exists(data_dir):
            # Cherche récursivement tous les .tif
            tif_files = glob.glob(os.path.join(data_dir, "**/*.tif"), recursive=True)
            found_files.extend(tif_files)
            if tif_files:
                print(f"✓ Trouvé {len(tif_files)} fichiers .tif dans {data_dir}/")
    
    # Si aucun fichier trouvé et téléchargement activé, tente de télécharger
    if not found_files and DRIVE_DOWNLOAD_ENABLED and not force_download:
        print("⚠️ Aucun fichier local, tentative de téléchargement depuis Drive...")
        if download_from_drive():
            return scan_all_rasters(force_download=True)  # Rescanne après téléchargement
    
    if not found_files:
        print("⚠️ Aucun fichier .tif trouvé dans:", DATA_DIRS)
        return raster_files
    
    # Classe les fichiers par type de variable
    for tif_path in found_files:
        filename = os.path.basename(tif_path)
        var_type = detect_variable_type(filename)
        
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
        "by_variable": summary,
        "sources": DATA_DIRS,
        "drive_enabled": DRIVE_DOWNLOAD_ENABLED
    })

# --------------------
# POST : Forcer le téléchargement depuis Google Drive
# --------------------
@environment_bp.route("/download-drive", methods=["POST"])
def force_download_drive():
    """Force le téléchargement des fichiers depuis Google Drive"""
    success = download_from_drive()
    
    if success:
        all_rasters = scan_all_rasters()
        return jsonify({
            "message": "Téléchargement terminé",
            "files_downloaded": sum(len(files) for files in all_rasters.values()),
            "by_variable": {k: len(v) for k, v in all_rasters.items()}
        })
    else:
        return jsonify({
            "error": "Échec du téléchargement",
            "message": "Vérifiez que gdown est installé et que l'URL Drive est correcte"
        }), 500

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
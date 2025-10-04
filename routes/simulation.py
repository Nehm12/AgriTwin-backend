# routes/simulation.py
from flask import Blueprint, jsonify, request
from models import Field, EnvironmentalData, Simulation
from db import db
from datetime import datetime, timedelta
import numpy as np

simulation_bp = Blueprint('simulation', __name__)

# --------------------
# Modèle de calcul du rendement
# --------------------
def calculate_yield(temperature, precipitation, humidity, ndvi, crop_type="maize"):
    """
    Calcule le rendement estimé basé sur les conditions environnementales
    
    Paramètres optimaux par culture (exemples FAO) :
    - Maïs : 20-30°C, 500-800mm précip, NDVI > 0.5
    - Riz : 25-35°C, 1200-1800mm, NDVI > 0.6
    - Manioc : 25-29°C, 1000-1500mm, NDVI > 0.4
    """
    
    # Paramètres par culture (basés sur données agronomiques FAO)
    CROP_PARAMS = {
        "Maïs": {"temp_opt": 25, "temp_range": 10, "prec_opt": 650, "ndvi_min": 0.5, "base_yield": 5.0},
        "Riz": {"temp_opt": 28, "temp_range": 8, "prec_opt": 1500, "ndvi_min": 0.6, "base_yield": 4.5},
        "Soja": {"temp_opt": 24, "temp_range": 9, "prec_opt": 600, "ndvi_min": 0.55, "base_yield": 3.0},
        "Blé": {"temp_opt": 20, "temp_range": 8, "prec_opt": 500, "ndvi_min": 0.5, "base_yield": 4.0},
        "Orge": {"temp_opt": 18, "temp_range": 7, "prec_opt": 450, "ndvi_min": 0.45, "base_yield": 3.5},
        "Pommes de terre": {"temp_opt": 17, "temp_range": 6, "prec_opt": 550, "ndvi_min": 0.5, "base_yield": 25.0},
        "Tomate": {"temp_opt": 22, "temp_range": 8, "prec_opt": 600, "ndvi_min": 0.6, "base_yield": 60.0},
        "Pomme": {"temp_opt": 16, "temp_range": 7, "prec_opt": 700, "ndvi_min": 0.55, "base_yield": 35.0},
        "Orange": {"temp_opt": 25, "temp_range": 8, "prec_opt": 1000, "ndvi_min": 0.6, "base_yield": 30.0},
        "Banane": {"temp_opt": 28, "temp_range": 6, "prec_opt": 1800, "ndvi_min": 0.65, "base_yield": 40.0},
        "Coton": {"temp_opt": 27, "temp_range": 7, "prec_opt": 700, "ndvi_min": 0.55, "base_yield": 2.5},
        "Arachide": {"temp_opt": 26, "temp_range": 8, "prec_opt": 650, "ndvi_min": 0.5, "base_yield": 2.0},
        "Café": {"temp_opt": 22, "temp_range": 6, "prec_opt": 1500, "ndvi_min": 0.6, "base_yield": 1.5},
        "Cacao": {"temp_opt": 25, "temp_range": 5, "prec_opt": 1800, "ndvi_min": 0.65, "base_yield": 1.2},
        "Pois": {"temp_opt": 18, "temp_range": 7, "prec_opt": 400, "ndvi_min": 0.45, "base_yield": 2.5}
    }
    
    params = CROP_PARAMS.get(crop_type, CROP_PARAMS["Maïs"])
    
    # Facteur température (Gaussien autour de l'optimum)
    temp_factor = np.exp(-((temperature - params["temp_opt"]) ** 2) / (2 * params["temp_range"] ** 2))
    
    # Facteur précipitation (sigmoïde)
    prec_factor = 1 / (1 + np.exp(-0.01 * (precipitation - params["prec_opt"])))
    
    # Facteur NDVI (santé végétale)
    ndvi_factor = max(0, min(1, (ndvi - params["ndvi_min"]) / (0.9 - params["ndvi_min"])))
    
    # Facteur humidité (optimum 60-80%)
    humidity_factor = 1 - abs(humidity - 70) / 70
    humidity_factor = max(0.5, min(1, humidity_factor))
    
    # Calcul final pondéré
    yield_estimate = params["base_yield"] * (
        0.35 * temp_factor +
        0.30 * prec_factor +
        0.25 * ndvi_factor +
        0.10 * humidity_factor
    )
    
    return round(yield_estimate, 2)

def calculate_risk_score(temperature, precipitation, ndvi):
    """Évalue le niveau de risque agricole"""
    risk_factors = []
    risk_score = 0
    
    # Risque de sécheresse
    if precipitation < 50:
        risk_score += 30
        risk_factors.append("Risque de sécheresse élevé")
    elif precipitation < 100:
        risk_score += 15
        risk_factors.append("Risque de sécheresse modéré")
    
    # Risque de chaleur excessive
    if temperature > 35:
        risk_score += 25
        risk_factors.append("Stress thermique sévère")
    elif temperature > 32:
        risk_score += 10
        risk_factors.append("Stress thermique modéré")
    
    # Santé végétale faible
    if ndvi < 0.3:
        risk_score += 30
        risk_factors.append("Végétation en mauvaise santé")
    elif ndvi < 0.5:
        risk_score += 15
        risk_factors.append("Végétation stressée")
    
    if not risk_factors:
        risk_factors.append("Conditions favorables")
    
    return min(100, risk_score), risk_factors

# --------------------
# POST : Créer une simulation
# --------------------
@simulation_bp.route("/", methods=["POST"])
def create_simulation():
    """
    Body attendu :
    {
        "field_id": 1,
        "crop_type": "maize",
        "planting_date": "2025-10-15",
        "harvest_date": "2026-02-15",
        "scenario": "current"
    }
    """
    data = request.get_json()
    
    try:
        field_id = data.get("field_id")
        crop_type = data.get("crop_type", "maize")
        planting_date = datetime.fromisoformat(data.get("planting_date"))
        harvest_date = datetime.fromisoformat(data.get("harvest_date"))
        scenario = data.get("scenario", "current")
        
        # Récupère le champ
        field = Field.query.get(field_id)
        if not field:
            return jsonify({"error": "Champ non trouvé"}), 404
        
        # Récupère les données environnementales récentes
        from routes.environment import scan_all_rasters, detect_variable_type
        from utils.raster_utils import extract_value_from_tiff
        
        all_rasters = scan_all_rasters()
        env_data = {}
        
        for var_type, file_list in all_rasters.items():
            if var_type != "unknown" and file_list:
                try:
                    value = extract_value_from_tiff(file_list[-1], field.lat, field.lon)
                    env_data[var_type] = value
                except:
                    env_data[var_type] = None
        
        # Valeurs par défaut si manquantes
        temperature = env_data.get("temperature", 27.0)
        precipitation = env_data.get("precipitation", 100.0)
        humidity = env_data.get("humidity", 70.0)
        ndvi = env_data.get("ndvi", 0.6)
        
        # Calcul du rendement et des risques
        yield_estimate = calculate_yield(temperature, precipitation, humidity, ndvi, crop_type)
        risk_score, risk_factors = calculate_risk_score(temperature, precipitation, ndvi)
        
        # Crée la simulation
        simulation = Simulation(
            field_id=field_id,
            crop_type=crop_type,
            planting_date=planting_date,
            harvest_date=harvest_date,
            predicted_yield=yield_estimate,
            scenario=scenario,
            risk_score=risk_score
        )
        
        db.session.add(simulation)
        db.session.commit()
        
        return jsonify({
            "message": "Simulation créée avec succès",
            "simulation_id": simulation.id,
            "results": {
                "field_name": field.name,
                "crop_type": crop_type,
                "predicted_yield_tons_per_ha": yield_estimate,
                "risk_score": risk_score,
                "risk_level": "Élevé" if risk_score > 50 else "Modéré" if risk_score > 25 else "Faible",
                "risk_factors": risk_factors,
                "environmental_conditions": {
                    "temperature_c": temperature,
                    "precipitation_mm": precipitation,
                    "humidity_percent": humidity,
                    "ndvi": ndvi
                },
                "planting_date": planting_date.date().isoformat(),
                "harvest_date": harvest_date.date().isoformat(),
                "growing_days": (harvest_date - planting_date).days
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --------------------
# GET : Récupérer toutes les simulations d'un champ
# --------------------
@simulation_bp.route("/field/<int:field_id>", methods=["GET"])
def get_field_simulations(field_id):
    """Liste toutes les simulations pour un champ donné"""
    simulations = Simulation.query.filter_by(field_id=field_id).all()
    
    if not simulations:
        return jsonify({"message": "Aucune simulation trouvée", "simulations": []}), 200
    
    results = []
    for sim in simulations:
        results.append({
            "id": sim.id,
            "crop_type": sim.crop_type,
            "predicted_yield": sim.predicted_yield,
            "risk_score": sim.risk_score,
            "planting_date": sim.planting_date.date().isoformat(),
            "harvest_date": sim.harvest_date.date().isoformat(),
            "created_at": sim.created_at.isoformat()
        })
    
    return jsonify({
        "field_id": field_id,
        "total_simulations": len(results),
        "simulations": results
    })

# --------------------
# GET : Récupérer une simulation spécifique
# --------------------
@simulation_bp.route("/<int:simulation_id>", methods=["GET"])
def get_simulation(simulation_id):
    """Détails d'une simulation"""
    sim = Simulation.query.get(simulation_id)
    
    if not sim:
        return jsonify({"error": "Simulation non trouvée"}), 404
    
    field = Field.query.get(sim.field_id)
    
    return jsonify({
        "id": sim.id,
        "field_name": field.name if field else "Inconnu",
        "field_id": sim.field_id,
        "crop_type": sim.crop_type,
        "predicted_yield_tons_per_ha": sim.predicted_yield,
        "risk_score": sim.risk_score,
        "planting_date": sim.planting_date.date().isoformat(),
        "harvest_date": sim.harvest_date.date().isoformat(),
        "scenario": sim.scenario,
        "created_at": sim.created_at.isoformat()
    })

# --------------------
# DELETE : Supprimer une simulation
# --------------------
@simulation_bp.route("/<int:simulation_id>", methods=["DELETE"])
def delete_simulation(simulation_id):
    """Supprime une simulation"""
    sim = Simulation.query.get(simulation_id)
    
    if not sim:
        return jsonify({"error": "Simulation non trouvée"}), 404
    
    db.session.delete(sim)
    db.session.commit()
    
    return jsonify({"message": "Simulation supprimée avec succès"})
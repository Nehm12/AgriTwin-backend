# routes/forecast.py
from flask import Blueprint, jsonify, request
from models import Field, EnvironmentalData, ForecastData
from db import db
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

forecast_bp = Blueprint('forecast', __name__)

# --------------------
# Prévision météo simple (sans Prophet pour éviter les dépendances lourdes)
# --------------------
def simple_forecast(historical_values, days_ahead=7):
    """Prévision basée sur moyenne mobile et tendance linéaire"""
    if len(historical_values) < 3:
        # Pas assez de données, retourne des valeurs constantes
        return [historical_values[-1] if historical_values else 0] * days_ahead
    
    # Calcul de la tendance (régression linéaire simple)
    x = np.arange(len(historical_values))
    coeffs = np.polyfit(x, historical_values, 1)
    trend = coeffs[0]
    
    # Prévision : dernière valeur + tendance
    last_value = historical_values[-1]
    forecast = []
    for i in range(1, days_ahead + 1):
        predicted = last_value + (trend * i)
        # Ajoute un peu de variation aléatoire
        noise = np.random.randn() * (np.std(historical_values) * 0.1)
        forecast.append(round(predicted + noise, 2))
    
    return forecast

def calculate_weather_forecast(field_id, days_ahead=7):
    """Génère des prévisions météo pour un champ depuis fichiers raster ou DB"""
    
    # Essaie d'abord de récupérer depuis les fichiers raster (local/Drive)
    try:
        from routes.environment import scan_all_rasters
        from utils.raster_utils import extract_value_from_tiff
        
        field = Field.query.get(field_id)
        if not field:
            return None
        
        all_rasters = scan_all_rasters()
        
        # Construit l'historique depuis les fichiers disponibles
        temps, precs, hums, ndvis = [], [], [], []
        
        for var_type, file_list in all_rasters.items():
            if var_type == "unknown" or not file_list:
                continue
            
            # Extrait depuis plusieurs fichiers (si disponibles) pour créer un historique
            for file_path in file_list[:30]:  # Max 30 fichiers pour historique
                try:
                    value = extract_value_from_tiff(file_path, field.lat, field.lon)
                    if value is not None:
                        if var_type == "temperature":
                            temps.append(value)
                        elif var_type == "precipitation":
                            precs.append(value)
                        elif var_type == "humidity":
                            hums.append(value)
                        elif var_type == "ndvi":
                            ndvis.append(value)
                except:
                    continue
        
        # Si on a des données depuis les rasters
        if any([temps, precs, hums, ndvis]):
            return {
                "temperature": simple_forecast(temps, days_ahead) if temps else [27.0] * days_ahead,
                "precipitation": simple_forecast(precs, days_ahead) if precs else [50.0] * days_ahead,
                "humidity": simple_forecast(hums, days_ahead) if hums else [70.0] * days_ahead,
                "ndvi": simple_forecast(ndvis, days_ahead) if ndvis else [0.6] * days_ahead
            }
    except Exception as e:
        print(f"Erreur extraction raster: {e}")
    
    # Fallback: utilise la base de données EnvironmentalData
    cutoff_date = datetime.now() - timedelta(days=30)
    historical_data = EnvironmentalData.query.filter(
        EnvironmentalData.field_id == field_id,
        EnvironmentalData.timestamp >= cutoff_date
    ).order_by(EnvironmentalData.timestamp.asc()).all()
    
    if not historical_data:
        # Pas de données du tout, utilise des valeurs par défaut
        return {
            "temperature": [27.0] * days_ahead,
            "precipitation": [50.0] * days_ahead,
            "humidity": [70.0] * days_ahead,
            "ndvi": [0.6] * days_ahead
        }
    
    # Extrait les valeurs historiques de la DB
    temps = [d.temperature for d in historical_data if d.temperature is not None]
    precs = [d.precipitation for d in historical_data if d.precipitation is not None]
    hums = [d.humidity for d in historical_data if d.humidity is not None]
    ndvis = [d.ndvi for d in historical_data if d.ndvi is not None]
    
    # Génère les prévisions
    return {
        "temperature": simple_forecast(temps, days_ahead) if temps else [27.0] * days_ahead,
        "precipitation": simple_forecast(precs, days_ahead) if precs else [50.0] * days_ahead,
        "humidity": simple_forecast(hums, days_ahead) if hums else [70.0] * days_ahead,
        "ndvi": simple_forecast(ndvis, days_ahead) if ndvis else [0.6] * days_ahead
    }

def estimate_yield(temp, prec, ndvi, humidity):
    """Calcule le rendement estimé (identique à ton modèle)"""
    if None in (temp, prec, ndvi, humidity):
        return None

    factor_temp = max(0, 1 - abs(temp - 27) / 15)
    factor_prec = min(prec / 100, 1)
    factor_ndvi = max(0, ndvi)
    factor_hum = min(humidity / 100, 1)

    yield_index = 100 * (
        0.4 * factor_temp + 
        0.3 * factor_prec + 
        0.2 * factor_ndvi + 
        0.1 * factor_hum
    )
    return round(yield_index, 2)

# --------------------
# GET : Prévisions météo pour un champ
# --------------------
@forecast_bp.route("/weather/<int:field_id>", methods=["GET"])
def get_weather_forecast(field_id):
    """Retourne les prévisions météo pour les 7 prochains jours"""
    
    field = Field.query.get(field_id)
    if not field:
        return jsonify({"error": "Champ non trouvé"}), 404
    
    days = request.args.get('days', 7, type=int)
    days = min(days, 30)  # Maximum 30 jours
    
    forecasts = calculate_weather_forecast(field_id, days)
    
    # Génère les dates futures
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") 
             for i in range(1, days + 1)]
    
    return jsonify({
        "field_id": field_id,
        "field_name": field.name,
        "forecast_days": days,
        "forecast": {
            "dates": dates,
            "temperature": forecasts["temperature"],
            "precipitation": forecasts["precipitation"],
            "humidity": forecasts["humidity"],
            "ndvi": forecasts["ndvi"]
        },
        "generated_at": datetime.now().isoformat()
    })

# --------------------
# GET : Prévision de rendement pour un champ
# --------------------
@forecast_bp.route("/yield/<int:field_id>", methods=["GET"])
def get_yield_forecast(field_id):
    """Calcule et retourne la prévision de rendement"""
    
    field = Field.query.get(field_id)
    if not field:
        return jsonify({"error": "Champ non trouvé"}), 404
    
    # Récupère les dernières données environnementales
    latest_data = EnvironmentalData.query.filter_by(
        field_id=field_id
    ).order_by(EnvironmentalData.timestamp.desc()).first()
    
    if not latest_data:
        return jsonify({
            "error": "Aucune donnée environnementale disponible",
            "message": "Ajoutez des données via /environment/<field_id>"
        }), 404
    
    # Calcul du rendement
    yield_estimate = estimate_yield(
        latest_data.temperature,
        latest_data.precipitation,
        latest_data.ndvi,
        latest_data.humidity
    )
    
    if yield_estimate is None:
        return jsonify({
            "error": "Données incomplètes",
            "message": "Certaines valeurs environnementales sont manquantes"
        }), 400
    
    # Sauvegarde la prévision
    forecast_entry = ForecastData(
        field_id=field_id,
        yield_estimate=yield_estimate,
        temperature_pred=latest_data.temperature,
        precipitation_pred=latest_data.precipitation,
        humidity_pred=latest_data.humidity,
        ndvi_pred=latest_data.ndvi
    )
    db.session.add(forecast_entry)
    db.session.commit()
    
    return jsonify({
        "field_id": field_id,
        "field_name": field.name,
        "yield_estimate": yield_estimate,
        "conditions": {
            "temperature_c": latest_data.temperature,
            "precipitation_mm": latest_data.precipitation,
            "humidity_percent": latest_data.humidity,
            "ndvi": latest_data.ndvi
        },
        "forecast_id": forecast_entry.id,
        "generated_at": datetime.now().isoformat()
    })

# --------------------
# GET : Prévisions complètes (météo + rendement)
# --------------------
@forecast_bp.route("/<int:field_id>", methods=["GET"])
def get_complete_forecast(field_id):
    """Retourne prévisions météo + rendement en une seule requête"""
    
    field = Field.query.get(field_id)
    if not field:
        return jsonify({"error": "Champ non trouvé"}), 404
    
    days = request.args.get('days', 7, type=int)
    
    # Prévisions météo
    weather_forecasts = calculate_weather_forecast(field_id, days)
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") 
             for i in range(1, days + 1)]
    
    # Prévision de rendement
    latest_data = EnvironmentalData.query.filter_by(
        field_id=field_id
    ).order_by(EnvironmentalData.timestamp.desc()).first()
    
    yield_estimate = None
    current_conditions = None
    
    if latest_data:
        yield_estimate = estimate_yield(
            latest_data.temperature,
            latest_data.precipitation,
            latest_data.ndvi,
            latest_data.humidity
        )
        current_conditions = {
            "temperature_c": latest_data.temperature,
            "precipitation_mm": latest_data.precipitation,
            "humidity_percent": latest_data.humidity,
            "ndvi": latest_data.ndvi
        }
    
    # Calcul du rendement moyen prévisionnel
    avg_temp = np.mean(weather_forecasts["temperature"])
    avg_prec = np.mean(weather_forecasts["precipitation"])
    avg_hum = np.mean(weather_forecasts["humidity"])
    avg_ndvi = np.mean(weather_forecasts["ndvi"])
    
    future_yield = estimate_yield(avg_temp, avg_prec, avg_ndvi, avg_hum)
    
    return jsonify({
        "field_id": field_id,
        "field_name": field.name,
        "current_conditions": current_conditions,
        "current_yield_estimate": yield_estimate,
        "weather_forecast": {
            "dates": dates,
            "temperature": weather_forecasts["temperature"],
            "precipitation": weather_forecasts["precipitation"],
            "humidity": weather_forecasts["humidity"],
            "ndvi": weather_forecasts["ndvi"]
        },
        "future_yield_estimate": future_yield,
        "generated_at": datetime.now().isoformat()
    })

# --------------------
# GET : Historique des prévisions
# --------------------
@forecast_bp.route("/history/<int:field_id>", methods=["GET"])
def get_forecast_history(field_id):
    """Retourne l'historique des prévisions pour un champ"""
    
    forecasts = ForecastData.query.filter_by(
        field_id=field_id
    ).order_by(ForecastData.timestamp.desc()).limit(30).all()
    
    if not forecasts:
        return jsonify({
            "field_id": field_id,
            "message": "Aucune prévision historique",
            "forecasts": []
        })
    
    results = []
    for f in forecasts:
        results.append({
            "id": f.id,
            "yield_estimate": f.yield_estimate,
            "temperature": f.temperature_pred,
            "precipitation": f.precipitation_pred,
            "humidity": f.humidity_pred,
            "ndvi": f.ndvi_pred,
            "timestamp": f.timestamp.isoformat()
        })
    
    return jsonify({
        "field_id": field_id,
        "total_forecasts": len(results),
        "forecasts": results
    })
from flask import Blueprint, jsonify
from utils.forecast_utils import forecast_weather
from utils.yield_forecast import estimate_yield
from models import ForecastData, Field
from datetime import datetime
import pandas as pd
import numpy as np

forecast_bp = Blueprint('forecast_bp', __name__)

@forecast_bp.route("/<int:field_id>", methods=["GET"])
def get_field_forecast(field_id):
    """
    Récupère les prévisions pour un champ spécifique.
    """
    field = Field.query.get(field_id)
    if not field:
        return jsonify({"error": "Field not found"}), 404

    # Données simulées pour les prévisions
    data = [
        {"date": datetime(2024, 9, i+1), "temperature": 26 + np.random.randn(),
         "precipitation": 50 + np.random.randn()*5, "humidity": 70 + np.random.randn()*2, "ndvi": 0.6 + np.random.randn()*0.05}
        for i in range(30)
    ]
    df = pd.DataFrame(data)

    forecasts = forecast_weather(df, days_ahead=15)

    avg_temp = df["temperature"].mean()
    avg_prec = df["precipitation"].mean()
    avg_hum = df["humidity"].mean()
    avg_ndvi = df["ndvi"].mean()

    yield_est = estimate_yield(avg_temp, avg_prec, avg_ndvi, avg_hum)

    return jsonify({
        "field_id": field_id,
        "forecast": {
            "yield_estimate": yield_est,
            "temperature_next_days": forecasts["temperature"]["yhat"].tolist(),
            "precipitation_next_days": forecasts["precipitation"]["yhat"].tolist(),
        }
    }), 200
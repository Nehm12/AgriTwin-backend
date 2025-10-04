# utils/forecast_utils.py
from prophet import Prophet
import pandas as pd

def forecast_weather(df, days_ahead=30):
    """
    Prévoit les tendances futures sur N jours.
    Le DataFrame doit contenir les colonnes : ['date', 'temperature', 'precipitation', 'humidity', 'ndvi']
    """
    forecasts = {}

    for variable in ['temperature', 'precipitation', 'humidity', 'ndvi']:
        df_var = df[['date', variable]].rename(columns={'date': 'ds', variable: 'y'})
        model = Prophet(daily_seasonality=True)
        model.fit(df_var)
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        forecasts[variable] = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days_ahead)

    return forecasts

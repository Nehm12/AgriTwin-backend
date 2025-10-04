from datetime import datetime
from db import db

# 👤 Utilisateur
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    lastname = db.Column(db.String(80), nullable=False)
    firstname = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200),  nullable=True)
    language = db.Column(db.String(10), default='fr')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔁 Relation avec les champs agricoles
    fields = db.relationship('Field', backref='user', lazy=True)


# 🌾 Champ agricole
class Field(db.Model):
    __tablename__ = 'field'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=True)
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    crop_type_id = db.Column(db.Integer, db.ForeignKey('crop_type.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    environment_data = db.relationship("EnvironmentalData", back_populates="field", lazy=True)
    forecast_data = db.relationship("ForecastData", backref="field", lazy=True)


# 🌻 Type de culture
class CropType(db.Model):
    __tablename__ = 'crop_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    optimal_temp = db.Column(db.Float, nullable=True)
    optimal_soil_moisture = db.Column(db.Float, nullable=True)
    cycle_days = db.Column(db.Integer, nullable=True)

    # 🔁 Relation inverse avec Field
    fields = db.relationship('Field', backref='crop_type', lazy=True)


# 💧 Historique des actions
class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    type = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Float, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    # Relation inverse
    field = db.relationship('Field', backref=db.backref('history', lazy=True))

# 🌐 Simulation des scénarios agricoles (VERSION ENRICHIE)
class Simulation(db.Model):
    __tablename__ = 'simulation'

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    
    # Informations sur la culture
    crop_type = db.Column(db.String(100), nullable=False)  # Nom de la culture (Maïs, Riz, etc.)
    planting_date = db.Column(db.Date, nullable=False)     # Date de plantation
    harvest_date = db.Column(db.Date, nullable=False)      # Date de récolte prévue
    
    # Résultats de la simulation
    predicted_yield = db.Column(db.Float, nullable=True)   # Rendement prédit (tonnes/ha)
    risk_score = db.Column(db.Integer, default=0)          # Score de risque (0-100)
    
    # Type de scénario (actuel, optimiste, pessimiste, changement climatique)
    scenario = db.Column(db.String(50), default='current') # 'current', 'optimistic', 'pessimistic', 'climate_change'
    
    # Conditions environnementales utilisées pour la simulation
    avg_temperature = db.Column(db.Float, nullable=True)   # Température moyenne (°C)
    avg_precipitation = db.Column(db.Float, nullable=True) # Précipitation moyenne (mm)
    avg_humidity = db.Column(db.Float, nullable=True)      # Humidité moyenne (%)
    avg_ndvi = db.Column(db.Float, nullable=True)          # NDVI moyen
    
    # Résumé détaillé (JSON ou texte)
    result_summary = db.Column(db.Text, nullable=True)     # Résumé détaillé de la simulation
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relation avec le champ
    field = db.relationship('Field', backref=db.backref('simulations', lazy=True))


# ⚠️ Alertes / Notifications
class Alert(db.Model):
    __tablename__ = 'alert'

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_via = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation avec le champ
    field = db.relationship('Field', backref=db.backref('alerts', lazy=True))


# 🤖 Chatbot messages ou logs
class ChatbotMessage(db.Model):
    __tablename__ = 'chatbot_message'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation avec l'utilisateur
    user = db.relationship('User', backref=db.backref('chatbot_messages', lazy=True))


# 🌍 Données environnementales
class EnvironmentalData(db.Model):
    __tablename__ = "environment_data"
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'))
    temperature = db.Column(db.Float)
    precipitation = db.Column(db.Float)
    humidity = db.Column(db.Float)
    ndvi = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    field = db.relationship("Field", back_populates="environment_data")


# 📊 Données de prévision
class ForecastData(db.Model):
    __tablename__ = "forecast_data"
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'))
    yield_estimate = db.Column(db.Float)
    temperature_pred = db.Column(db.Float)
    precipitation_pred = db.Column(db.Float)
    humidity_pred = db.Column(db.Float)
    ndvi_pred = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


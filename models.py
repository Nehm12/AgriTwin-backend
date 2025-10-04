from datetime import datetime
from db import db

# 👤 Utilisateur
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    lastname = db.Column(db.String(80), nullable=False)   # Nom obligatoire
    firstname = db.Column(db.String(80), nullable=True)   # Prénom facultatif
    email = db.Column(db.String(120), unique=True, nullable=True)  # facultatif
    phone = db.Column(db.String(20), unique=True, nullable=False)  # obligatoire
    password = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(10), default='fr')     # langue par défaut
    created_at = db.Column(db.DateTime, default=datetime.utcnow)   # timestamp UTC

    # 🔁 Relation avec les champs agricoles
    fields = db.relationship('Field', backref='user', lazy=True)


# 🌾 Champ agricole
class Field(db.Model):
    __tablename__ = 'field'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Nom du champ (optionnel)
    name = db.Column(db.String(100), nullable=True)

    # Coordonnées du champ (issues de la carte)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=True)  # superficie en ha ou m², calculée depuis la carte

    # Informations géographiques (extraites automatiquement)
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)

    # Type de culture associé (clé étrangère)
    crop_type_id = db.Column(db.Integer, db.ForeignKey('crop_type.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 🌻 Type de culture
class CropType(db.Model):
    __tablename__ = 'crop_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # nom unique de la culture (ex: Maïs, Riz, Tomate)

    # Données agroclimatiques provenant des datasets
    optimal_temp = db.Column(db.Float, nullable=True)            # Température optimale (°C)
    optimal_soil_moisture = db.Column(db.Float, nullable=True)   # Humidité du sol optimale (%)
    cycle_days = db.Column(db.Integer, nullable=True)            # Durée du cycle en jours

    # 🔁 Relation inverse avec Field
    fields = db.relationship('Field', backref='crop_type', lazy=True)


# 💧 Historique des actions (Irrigation, Fertilisation, Alerte, etc.)
class History(db.Model):
    __tablename__ = 'history'

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)

    # Type d'action : 'irrigation', 'fertilisation', 'alerte', 'semis', 'recolte'
    type = db.Column(db.String(30), nullable=False)

    # Quantité associée (litres, kg, etc.)
    quantity = db.Column(db.Float, nullable=True)

    # Date automatique (UTC)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Notes / détails additionnels
    notes = db.Column(db.Text, nullable=True)

    # Relation inverse
    field = db.relationship('Field', backref=db.backref('history', lazy=True))

# 🌐 Simulation des scénarios agricoles
class Simulation(db.Model):
    __tablename__ = 'simulation'

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    scenario_type = db.Column(db.String(50), nullable=False)  # ex: 'irrigation', 'fertilisation', 'sécheresse'
    result_summary = db.Column(db.Text, nullable=True)         # description du résultat de la simulation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation avec le champ
    field = db.relationship('Field', backref=db.backref('simulations', lazy=True))


# ⚠️ Alertes / Notifications
class Alert(db.Model):
    __tablename__ = 'alert'

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)           # ex: 'alerte météo', 'alerte irrigation'
    message = db.Column(db.Text, nullable=False)
    sent_via = db.Column(db.String(20), nullable=True)        # ex: SMS, WhatsApp, USSD
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation avec le champ
    field = db.relationship('Field', backref=db.backref('alerts', lazy=True))


# 🤖 Chatbot messages ou logs
class ChatbotMessage(db.Model):
    __tablename__ = 'chatbot_message'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)             # message envoyé par l'utilisateur
    response = db.Column(db.Text, nullable=True)             # réponse générée par le bot
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation avec l'utilisateur
    user = db.relationship('User', backref=db.backref('chatbot_messages', lazy=True))
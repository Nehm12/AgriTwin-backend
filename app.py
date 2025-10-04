from flask import Flask, jsonify, render_template
from flask_cors import CORS
from db import init_db
from models import User, Field, CropType, History

# Import des routes
from routes.users import user_bp
from routes.fields import field_bp
from routes.history import history_bp
from routes.simulation import simulation_bp
from routes.alert import alert_bp
from routes.chatbot import chatbot_bp
from routes.forecast import forecast_bp
from routes.environment import environment_bp

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)

# Initialisation de la base de données
db = init_db(app)

# Enregistrement des blueprints
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(field_bp, url_prefix='/fields')
app.register_blueprint(history_bp, url_prefix='/history')
app.register_blueprint(simulation_bp, url_prefix='/simulation')
app.register_blueprint(alert_bp, url_prefix='/alerts')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
app.register_blueprint(forecast_bp, url_prefix='/forecast')
app.register_blueprint(environment_bp, url_prefix='/environment')

# Flag pour initialisation unique
initialized = False
initialization_message = ""

@app.before_request
def create_tables():
    """
    Création automatique des tables et insertion des cultures à la première requête.
    """
    global initialized, initialization_message
    if not initialized:
        with app.app_context():
            db.create_all()

            # Liste des cultures à ajouter
            crops = [
                {'name': 'Maïs', 'optimal_temp': 25, 'optimal_soil_moisture': 0.3, 'cycle_days': 120},
                {'name': 'Riz', 'optimal_temp': 28, 'optimal_soil_moisture': 0.5, 'cycle_days': 150},
                {'name': 'Soja', 'optimal_temp': 24, 'optimal_soil_moisture': 0.35, 'cycle_days': 100},
                {'name': 'Blé', 'optimal_temp': 20, 'optimal_soil_moisture': 0.25, 'cycle_days': 110},
                {'name': 'Orge', 'optimal_temp': 18, 'optimal_soil_moisture': 0.22, 'cycle_days': 90},
                {'name': 'Pommes de terre', 'optimal_temp': 17, 'optimal_soil_moisture': 0.4, 'cycle_days': 120},
                {'name': 'Tomate', 'optimal_temp': 22, 'optimal_soil_moisture': 0.35, 'cycle_days': 90},
                {'name': 'Pomme', 'optimal_temp': 16, 'optimal_soil_moisture': 0.3, 'cycle_days': 150},
                {'name': 'Orange', 'optimal_temp': 25, 'optimal_soil_moisture': 0.3, 'cycle_days': 180},
                {'name': 'Banane', 'optimal_temp': 28, 'optimal_soil_moisture': 0.5, 'cycle_days': 200},
                {'name': 'Coton', 'optimal_temp': 27, 'optimal_soil_moisture': 0.3, 'cycle_days': 150},
                {'name': 'Arachide', 'optimal_temp': 26, 'optimal_soil_moisture': 0.35, 'cycle_days': 120},
                {'name': 'Café', 'optimal_temp': 22, 'optimal_soil_moisture': 0.4, 'cycle_days': 180},
                {'name': 'Cacao', 'optimal_temp': 25, 'optimal_soil_moisture': 0.45, 'cycle_days': 180},
                {'name': 'Pois', 'optimal_temp': 18, 'optimal_soil_moisture': 0.25, 'cycle_days': 80}
            ]

            added_count = 0
            for crop in crops:
                exists = CropType.query.filter_by(name=crop['name']).first()
                if not exists:
                    db.session.add(CropType(**crop))
                    added_count += 1

            db.session.commit()
            if added_count > 0:
                initialization_message = f"{added_count} cultures ajoutées à la base de données."
            else:
                initialization_message = "Toutes les cultures sont déjà présentes."

        initialized = True

# Route d'accueil
@app.route('/')
def index():
    return jsonify({
        "message": "AgriTwin Backend API running",
        "initialization": initialization_message,
        "endpoints": {
            "users": "/users/",
            "fields": "/fields/",
            "history": "/history/",
            "simulation": "/simulation/",
            "alerts": "/alerts/",
            "chatbot": "/chatbot/",
            "forecast": "/forecast/",
            "environment": "/environment/"
        },
        "check_all": "/api-status"
    })

@app.route('/api-status-json')
def api_status_json():
    """Vérifie le status de toutes les APIs"""
    endpoints = {
        "Users API": "/users/",
        "Fields API": "/fields/",
        "History API": "/history/",
        "Simulation API": "/simulation/",
        "Alerts API": "/alerts/",
        "Chatbot API": "/chatbot/",
        "Forecast API": "/forecast/",
        "Environment API": "/environment/"
    }

    status = {}
    with app.test_client() as client:
        for name, path in endpoints.items():
            try:
                response = client.get(path)
                if response.status_code in [200, 404]:  # 404 normal si pas de données
                    status[name] = {"path": path, "status": "OK", "code": response.status_code}
                else:
                    status[name] = {"path": path, "status": "Error", "code": response.status_code}
            except Exception as e:
                status[name] = {"path": path, "status": f"Error: {str(e)}"}

    return jsonify({
        "message": "API Status Check",
        "status": status
    })

@app.route('/api-status')
def api_status_page():
    return render_template('api_status.html')

# Lancement du serveur
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
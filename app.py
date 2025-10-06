from flask import Flask, jsonify
from flask_cors import CORS
from db import init_db, db
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
from routes.crops import crop_bp

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)

# Initialisation de la base de données
init_db(app)

# Enregistrement des blueprints
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(field_bp, url_prefix='/fields')
app.register_blueprint(history_bp, url_prefix='/history')
app.register_blueprint(simulation_bp, url_prefix='/simulation')
app.register_blueprint(alert_bp, url_prefix='/alerts')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
app.register_blueprint(forecast_bp, url_prefix='/forecast')
app.register_blueprint(environment_bp, url_prefix='/environment')
app.register_blueprint(crop_bp, url_prefix='/crops')

# Variable pour tracking du seeding
_seeded = False

@app.before_request
def seed_on_first_request():
    """Seed les données lors de la première requête"""
    global _seeded
    if not _seeded:
        try:
            if CropType.query.count() == 0:
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
                
                for crop in crops:
                    db.session.add(CropType(**crop))
                
                db.session.commit()
                print(f"Seeded {len(crops)} crop types")
        except Exception as e:
            print(f"Seeding error: {e}")
        finally:
            _seeded = True

@app.route('/')
def index():
    return jsonify({
        "message": "AgriTwin Backend API running",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users/",
            "fields": "/fields/",
            "history": "/history/",
            "simulation": "/simulation/",
            "alerts": "/alerts/",
            "chatbot": "/chatbot/",
            "forecast": "/forecast/",
            "environment": "/environment/",
            "crops": "/crops/"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
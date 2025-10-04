from flask import Flask, jsonify
from flask_cors import CORS
from db import init_db
from models import User, Field, CropType, History


from routes.users import user_bp
from routes.fields import field_bp
from routes.history import history_bp
from routes.simulation import simulation_bp
from routes.alert import alert_bp
from routes.chatbot import chatbot_bp


# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)

# Initialisation de la base de données
db = init_db(app)

# Flag pour que l'initialisation ne s'exécute qu'une seule fois
initialized = False
initialization_message = ""

app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(field_bp, url_prefix='/fields')
app.register_blueprint(history_bp, url_prefix='/history')
app.register_blueprint(simulation_bp, url_prefix='/simulation')
app.register_blueprint(alert_bp, url_prefix='/alerts')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')



# Flag pour que l'initialisation ne s'exécute qu'une seule fois
initialized = False
initialization_message = ""

@app.before_request
def create_tables():
    global initialized, initialization_message
    if not initialized:
        with app.app_context():
            # Création de toutes les tables
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

            # Ajouter uniquement les cultures qui n'existent pas encore
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
                initialization_message = "Toutes les cultures sont déjà présentes — aucune insertion nécessaire."

        initialized = True

# Route d'accueil
@app.route('/')
def index():
    return jsonify({
        "message": "AgriTwin Backend API running",
        "initialization": initialization_message
    })

# Lancement du serveur
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

from flask_sqlalchemy import SQLAlchemy
from db import db
import os

db = SQLAlchemy()

def init_db(app):
    """Configure et initialise la base de données"""
    # Récupérer l'URL de la base de données
    database_url = os.environ.get('DATABASE_URL')
    
    # Render utilise postgres://, SQLAlchemy 2.0 requiert postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///agritwin.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialiser l'extension avec l'app
    db.init_app(app)
    
    # Créer les tables
    with app.app_context():
        db.create_all()
        print("✓ Base de données initialisée")
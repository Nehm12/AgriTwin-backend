from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    # Récupérer l'URL de la base de données depuis les variables d'environnement
    database_url = os.environ.get('DATABASE_URL')
    
    # Render utilise postgres://, SQLAlchemy 2.0 requiert postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Utiliser PostgreSQL en production, SQLite en local
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///agritwin.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Créer les tables
    with app.app_context():
        try:
            print("Création des tables...")
            db.create_all()
            print("Tables créées avec succès !")
        except Exception as e:
            print(f"Erreur lors de la création des tables : {e}")
    
    return db
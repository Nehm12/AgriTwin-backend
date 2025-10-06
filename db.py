from flask_sqlalchemy import SQLAlchemy

# Instance globale de la base de données
db = SQLAlchemy()

def init_db(app):
    # Configuration de la base SQLite locale et pg en production
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///agritwin.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Lier SQLAlchemy à l’application Flask
    db.init_app(app)
    return db

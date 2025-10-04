from flask import Blueprint, request, jsonify
from models import History
from db import db

history_bp = Blueprint('history_bp', __name__)

# Ajouter un historique
@history_bp.route('/', methods=['POST'])
def create_history():
    data = request.json
    hist = History(
        field_id=data['field_id'],
        type=data['type'],
        quantity=data.get('quantity'),
        notes=data.get('notes')
    )
    db.session.add(hist)
    db.session.commit()
    return jsonify({"message": "Historique créé", "id": hist.id})

# Lister tous les historiques
@history_bp.route('/', methods=['GET'])
def get_history():
    records = History.query.all()
    return jsonify([{
        "id": r.id,
        "field_id": r.field_id,
        "type": r.type,
        "quantity": r.quantity,
        "date": r.date,
        "notes": r.notes
    } for r in records])

# Récupérer un historique par id
@history_bp.route('/<int:history_id>', methods=['GET'])
def get_history_item(history_id):
    r = History.query.get_or_404(history_id)
    return jsonify({
        "id": r.id,
        "field_id": r.field_id,
        "type": r.type,
        "quantity": r.quantity,
        "date": r.date,
        "notes": r.notes
    })

# Mettre à jour un historique
@history_bp.route('/<int:history_id>', methods=['PUT'])
def update_history(history_id):
    r = History.query.get_or_404(history_id)
    data = request.json
    r.type = data.get('type', r.type)
    r.quantity = data.get('quantity', r.quantity)
    r.notes = data.get('notes', r.notes)
    db.session.commit()
    return jsonify({"message": "Historique mis à jour"})

# Supprimer un historique
@history_bp.route('/<int:history_id>', methods=['DELETE'])
def delete_history(history_id):
    r = History.query.get_or_404(history_id)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "Historique supprimé"})

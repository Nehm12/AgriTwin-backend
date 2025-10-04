from flask import Blueprint, request, jsonify
from models import Alert
from db import db

alert_bp = Blueprint('alert_bp', __name__)

@alert_bp.route('/', methods=['POST'])
def create_alert():
    data = request.json
    alert = Alert(
        field_id=data['field_id'],
        type=data['type'],
        message=data['message'],
        sent_via=data.get('sent_via')
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({"message": "Alerte créée", "id": alert.id})

@alert_bp.route('/', methods=['GET'])
def get_alerts():
    alerts = Alert.query.all()
    return jsonify([{
        "id": a.id,
        "field_id": a.field_id,
        "type": a.type,
        "message": a.message,
        "sent_via": a.sent_via,
        "created_at": a.created_at
    } for a in alerts])

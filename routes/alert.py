from flask import Blueprint, request, jsonify
from models import Alert, Field, AlertRead
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
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return jsonify([{
        "id": a.id,
        "field_id": a.field_id,
        "type": a.type,
        "message": a.message,
        "sent_via": a.sent_via,
        "created_at": a.created_at.isoformat()
    } for a in alerts])

@alert_bp.route('/field/<int:field_id>', methods=['GET'])
def get_alerts_by_field(field_id):
    alerts = Alert.query.filter_by(field_id=field_id).order_by(Alert.created_at.desc()).all()
    return jsonify([{
        "id": a.id,
        "field_id": a.field_id,
        "type": a.type,
        "message": a.message,
        "sent_via": a.sent_via,
        "created_at": a.created_at.isoformat()
    } for a in alerts])

@alert_bp.route('/user/<int:user_id>', methods=['GET'])
def get_alerts_by_user(user_id):
    # Récupérer les champs de l'utilisateur et leurs alertes
    field_ids = [f.id for f in Field.query.filter_by(user_id=user_id).all()]
    if not field_ids:
        return jsonify([])
    alerts = Alert.query.filter(Alert.field_id.in_(field_ids)).order_by(Alert.created_at.desc()).all()
    alert_ids = [a.id for a in alerts]
    read_map = set()
    if alert_ids:
        reads = AlertRead.query.filter(AlertRead.user_id == user_id, AlertRead.alert_id.in_(alert_ids)).all()
        read_map = set(r.alert_id for r in reads)
    return jsonify([{
        "id": a.id,
        "field_id": a.field_id,
        "type": a.type,
        "message": a.message,
        "sent_via": a.sent_via,
        "created_at": a.created_at.isoformat(),
        "read": (a.id in read_map)
    } for a in alerts])

@alert_bp.route('/read', methods=['POST'])
def mark_alert_read():
    data = request.json or {}
    alert_id = data.get('alert_id')
    user_id = data.get('user_id')
    if not alert_id or not user_id:
        return jsonify({"error": "alert_id et user_id requis"}), 400
    exists = AlertRead.query.filter_by(alert_id=alert_id, user_id=user_id).first()
    if exists:
        return jsonify({"message": "Déjà marqué comme lu"})
    read = AlertRead(alert_id=alert_id, user_id=user_id)
    db.session.add(read)
    db.session.commit()
    return jsonify({"message": "Alerte marquée comme lue"})

@alert_bp.route('/user/<int:user_id>/mark-all-read', methods=['POST'])
def mark_all_read(user_id):
    field_ids = [f.id for f in Field.query.filter_by(user_id=user_id).all()]
    if not field_ids:
        return jsonify({"message": "Aucune alerte"})
    alerts = Alert.query.filter(Alert.field_id.in_(field_ids)).all()
    alert_ids = set(a.id for a in alerts)
    existing = AlertRead.query.filter(AlertRead.user_id == user_id, AlertRead.alert_id.in_(list(alert_ids))).all()
    existing_ids = set(r.alert_id for r in existing)
    to_create = [AlertRead(alert_id=aid, user_id=user_id) for aid in (alert_ids - existing_ids)]
    if to_create:
        db.session.bulk_save_objects(to_create)
        db.session.commit()
    return jsonify({"message": "Toutes les alertes marquées comme lues", "count": len(to_create)})

@alert_bp.route('/user/<int:user_id>/unread-count', methods=['GET'])
def unread_count(user_id):
    field_ids = [f.id for f in Field.query.filter_by(user_id=user_id).all()]
    if not field_ids:
        return jsonify({"unread": 0})
    total = Alert.query.filter(Alert.field_id.in_(field_ids)).count()
    read_count = db.session.query(AlertRead.alert_id).filter(AlertRead.user_id == user_id).distinct().count()
    return jsonify({"unread": max(0, total - read_count)})

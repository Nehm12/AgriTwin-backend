from flask import Blueprint, request, jsonify
from models import NotificationPreference
from db import db

notification_bp = Blueprint('notification_bp', __name__)

@notification_bp.route('/preferences/<int:user_id>', methods=['GET'])
def get_preferences(user_id):
    pref = NotificationPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        # valeurs par défaut si non configuré
        return jsonify({
            "user_id": user_id,
            "irrigation": True,
            "fertilization": True,
            "climate": True,
            "pestDisease": True,
            "in_app": True,
            "sms": False,
            "whatsapp": False,
            "email": False
        })
    return jsonify({
        "user_id": user_id,
        "irrigation": pref.irrigation,
        "fertilization": pref.fertilization,
        "climate": pref.climate,
        "pestDisease": pref.pestDisease,
        "in_app": pref.in_app,
        "sms": pref.sms,
        "whatsapp": pref.whatsapp,
        "email": pref.email
    })

@notification_bp.route('/preferences/<int:user_id>', methods=['PUT'])
def update_preferences(user_id):
    data = request.json or {}
    pref = NotificationPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        pref = NotificationPreference(user_id=user_id)
        db.session.add(pref)

    for key in ["irrigation", "fertilization", "climate", "pestDisease", "in_app", "sms", "whatsapp", "email"]:
        if key in data:
            setattr(pref, key, bool(data[key]))

    db.session.commit()
    return jsonify({"message": "Préférences mises à jour"})

import os
from typing import List, Optional
from db import db
from models import Alert, Field, User, NotificationPreference


def _get_user_by_field(field_id: int) -> Optional[User]:
    try:
        field = Field.query.get(field_id)
        if not field:
            return None
        user = User.query.get(field.user_id)
        return user
    except Exception:
        return None


def send_email(user: User, subject: str, body: str) -> None:
    """
    Stub d'envoi d'e-mail. Intégrez ici un SMTP (ex: smtplib) ou un service (SendGrid, SES).
    """
    if not user or not user.email:
        return
    # Exemple de log. Remplacez par un envoi réel si config dispo.
    print(f"[EMAIL] To: {user.email} | Subject: {subject} | Body: {body}")


def send_sms(user: User, message: str) -> None:
    """
    Stub d'envoi de SMS. Intégrez ici Twilio ou autre gateway SMS.
    """
    if not user or not user.phone:
        return
    print(f"[SMS] To: {user.phone} | Message: {message}")


def send_whatsapp(user: User, message: str) -> None:
    """
    Stub d'envoi WhatsApp. Intégrez ici WhatsApp Cloud API / Twilio WhatsApp.
    """
    if not user or not user.phone:
        return
    print(f"[WHATSAPP] To: {user.phone} | Message: {message}")


def _apply_user_preferences(user: Optional[User], type: str, requested_channels: List[str]) -> List[str]:
    if not user:
        return requested_channels
    pref = NotificationPreference.query.filter_by(user_id=user.id).first()
    if not pref:
        return requested_channels

    category_map = {
        'irrigation': 'irrigation',
        'fertilization': 'fertilization',
        'climate': 'climate',
        'pestDisease': 'pestDisease',
        'ndvi_low': 'pestDisease',
        'frost_warning': 'climate',
        'frost_warning_forecast': 'climate',
        'heat_warning': 'climate',
        'heat_warning_forecast': 'climate',
        'heavy_rain': 'climate',
        'heavy_rain_forecast': 'climate',
        'drought_risk': 'climate',
        'drought_risk_forecast': 'climate',
        'high_wind': 'climate',
        'yield_forecast_generated': 'fertilization',
        'low_yield_current': 'fertilization',
        'low_yield_forecast': 'fertilization',
        'high_risk': 'climate',
        'simulation_result': 'fertilization'
    }
    category = category_map.get(type, None)

    allowed_channels = []
    if category:
        category_enabled = getattr(pref, category, True)
        if not category_enabled:
            if pref.in_app and 'in_app' in requested_channels:
                allowed_channels.append('in_app')
            return allowed_channels

    for ch in requested_channels:
        if ch == 'in_app' and pref.in_app:
            allowed_channels.append(ch)
        if ch == 'sms' and pref.sms:
            allowed_channels.append(ch)
        if ch == 'email' and pref.email:
            allowed_channels.append(ch)
        if ch == 'whatsapp' and pref.whatsapp:
            allowed_channels.append(ch)

    if not allowed_channels and pref.in_app and 'in_app' in requested_channels:
        allowed_channels.append('in_app')

    return allowed_channels


def create_alert(field_id: int, type: str, message: str, channels: Optional[List[str]] = None) -> Optional[int]:
    """
    Crée une alerte en base (in-app par défaut) et envoie via canaux optionnels.
    channels peut contenir: 'in_app', 'email', 'sms', 'whatsapp'.
    """
    try:
        if channels is None or len(channels) == 0:
            channels = ["in_app"]

        # Applique les préférences utilisateur
        user = _get_user_by_field(field_id)
        channels = _apply_user_preferences(user, type, channels)

        # Toujours créer une alerte en base si au moins in_app
        sent_via = ",".join(channels)
        alert = Alert(field_id=field_id, type=type, message=message, sent_via=sent_via)
        db.session.add(alert)
        db.session.commit()

        # Envois multi-canaux (stubs)
        subject = f"AgriTwin - {type.replace('_', ' ').title()}"
        if 'email' in channels:
            send_email(user, subject, message)
        if 'sms' in channels:
            send_sms(user, message)
        if 'whatsapp' in channels:
            send_whatsapp(user, message)

        return alert.id
    except Exception as e:
        db.session.rollback()
        print(f"[Notification] Erreur create_alert: {e}")
        return None

# backend/whatsapp.py
"""
Módulo para enviar mensajes de WhatsApp usando Twilio API.
"""
from twilio.rest import Client
import os

def enviar_whatsapp(mensaje, destinatario=None):
    """
    Envía un mensaje de WhatsApp usando Twilio.
    destinatario: número en formato internacional, ej: 'whatsapp:+549XXXXXXXXXX'
    """
    # Configuración desde variables de entorno o hardcodear para pruebas
    account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'TU_SID_AQUI')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'TU_TOKEN_AQUI')
    from_whatsapp = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')  # Twilio sandbox
    to_whatsapp = destinatario or os.getenv('TWILIO_WHATSAPP_TO', 'whatsapp:+549XXXXXXXXXX')

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=mensaje,
        from_=from_whatsapp,
        to=to_whatsapp
    )
    return message.sid

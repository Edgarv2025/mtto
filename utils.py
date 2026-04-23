import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from flask import session, redirect, url_for, flash
from db import get_db_connection
from config import Config

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "role" not in session or session["role"] not in roles:
                flash("Acceso denegado: no tienes permisos suficientes.", "error")
                return redirect(url_for("reports.dashboard"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def send_email(subject, body, to_email):
    if not to_email:
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = Config.EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Error enviando correo:", e)

def notify_status_change(item_id, new_status, custom_to_email=None):
    conn = get_db_connection()
    item = conn.execute(
        """
        SELECT 
            i.*, 
            p.description, 
            r.consecutive_no,
            r.requested_by
        FROM maintenance_items i
        LEFT JOIN products p ON i.product_code = p.code
        JOIN maintenance_records r ON i.record_id = r.id
        WHERE i.id = ?
    """,
        (item_id,),
    ).fetchone()
    conn.close()

    if not item:
        return

    subject = f"Actualización Req #{item['consecutive_no']}"
    body = f"""
    <h3>Actualización de estado</h3>
    <p><b>Requerimiento:</b> {item['consecutive_no']}</p>
    <p><b>Producto:</b> {item['product_code']} - {item['description']}</p>
    <p><b>Estado nuevo:</b> {new_status}</p>
    <br>
    <p>Sistema de mantenimiento</p>
    """
    
    # Priority for email target: custom explicitly passed -> else fallback global Config
    target_email = custom_to_email or Config.DEFAULT_NOTIFY_EMAIL
    
    send_email(subject, body, target_email)

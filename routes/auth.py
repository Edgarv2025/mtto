from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection
from utils import login_required, role_required
import io
import csv

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user is None:
            flash("Usuario incorrecto.", "error")
        elif not check_password_hash(user["password_hash"], password):
            flash("Contraseña incorrecta.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("reports.dashboard"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/users", methods=("GET", "POST"))
@login_required
@role_required("ADMIN", "COMPRAS")
def users():
    conn = get_db_connection()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "CREATE":
            username = request.form.get("username")
            password = request.form.get("password")
            role = request.form.get("role")
            email = request.form.get("email")

            if not username or not password or not role or not email:
                flash("Todos los campos (incluyendo Email) son requeridos para nuevos usuarios", "error")
            else:
                try:
                    hash_pw = generate_password_hash(password)
                    conn.execute(
                        "INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
                        (username, hash_pw, role, email),
                    )
                    conn.commit()
                    flash(f"Usuario {username} creado exitosamente.", "success")
                except sqlite3.IntegrityError:
                    flash(f"El usuario {username} ya existe.", "error")

        elif action == "UPDATE_ROLE":
            user_id = request.form.get("user_id")
            role = request.form.get("role")
            email = request.form.get("email")
            # En caso de que se pase sin email desde un navegador viejo, no actualizamos a nulo
            if email:
                conn.execute("UPDATE users SET role = ?, email = ? WHERE id = ?", (role, email, user_id))
            else:
                conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()
            flash("Datos del usuario actualizados exitosamente.", "success")

        elif action == "DELETE":
            user_id = request.form.get("user_id")
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            flash("Usuario eliminado.", "success")

        elif action == "UPLOAD_CSV":
            file = request.files.get("file")
            if file and file.filename.endswith(".csv"):
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.reader(stream)
                next(csv_input, None)  # Saltar cabecera
                count = 0
                for row in csv_input:
                    if len(row) >= 2:
                        u, r = row[0].strip(), row[1].strip()
                        # Default email for CSV imports if not specified in 3rd col
                        e = row[2].strip() if len(row) > 2 else "evasquez@imasa.com.co"
                        pw_hash = generate_password_hash(f"{u}123")
                        try:
                            import sqlite3
                            conn.execute(
                                "INSERT INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
                                (u, pw_hash, r.upper(), e),
                            )
                            count += 1
                        except sqlite3.IntegrityError:
                            pass
                conn.commit()
                flash(f"{count} usuarios importados exitosamente.", "success")

    all_users = conn.execute(
        "SELECT id, username, role, email FROM users ORDER BY username"
    ).fetchall()
    conn.close()

    roles_list = [
        "ADMIN",
        "JEFE_AREA",
        "GT",
        "COMPRAS",
        "GR",
        "ALMACEN",
    ]
    return render_template("users.html", users=all_users, roles=roles_list)

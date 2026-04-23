from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from db import get_db_connection
from utils import login_required, role_required
import io
import csv
import sqlite3

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route("/suppliers", methods=("GET", "POST"))
@login_required
def suppliers():
    if session.get("role") not in ["ADMIN", "COMPRAS"]:
        return redirect(url_for("reports.dashboard"))

    conn = get_db_connection()

    if request.method == "POST":
        if session.get("role") not in ["ADMIN", "COMPRAS"]:
            flash("Acceso denegado. Solo ADMIN o COMPRAS pueden gestionar proveedores.", "error")
            return redirect(url_for("suppliers.suppliers"))

        action = request.form.get("action", "CREATE")

        if action == "CREATE":
            nit = request.form.get("nit")
            name = request.form.get("name")
            contact_name = request.form.get("contact_name") or " "
            phone = request.form.get("phone") or " "

            if not nit or not name:
                flash("NIT y Nombre son requeridos", "error")
            else:
                try:
                    conn.execute(
                        "INSERT INTO suppliers (nit, name, contact_name, phone) VALUES (?, ?, ?, ?)",
                        (nit, name, contact_name, phone),
                    )
                    conn.commit()
                    flash("Proveedor creado exitosamente.", "success")
                except sqlite3.IntegrityError:
                    flash(f"El NIT {nit} ya existe en la base de datos.", "error")

        elif action == "EDIT":
            sid = request.form.get("id")
            name = request.form.get("name")
            contact_name = request.form.get("contact_name")
            phone = request.form.get("phone")

            conn.execute(
                "UPDATE suppliers SET name = ?, contact_name = ?, phone = ? WHERE id = ?",
                (name, contact_name, phone, sid),
            )
            conn.commit()
            flash("Proveedor actualizado.", "success")

        elif action == "DELETE":
            sid = request.form.get("id")
            conn.execute("DELETE FROM suppliers WHERE id = ?", (sid,))
            conn.commit()
            flash("Proveedor eliminado.", "success")

        elif action == "UPLOAD_CSV":
            file = request.files.get("file")
            if file and file.filename.endswith(".csv"):
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.reader(stream)
                next(csv_input, None)
                count = 0

                for row in csv_input:
                    if len(row) >= 2:
                        nit = row[0].strip()
                        name = row[1].strip()
                        contact_name = row[2].strip() if len(row) > 2 else ""
                        phone = row[3].strip() if len(row) > 3 else ""

                        if nit and name:
                            try:
                                conn.execute(
                                    "INSERT INTO suppliers (nit, name, contact_name, phone) VALUES (?, ?, ?, ?)",
                                    (nit, name, contact_name, phone),
                                )
                                count += 1
                            except sqlite3.IntegrityError:
                                pass
                conn.commit()
                flash(f"{count} proveedores importados exitosamente.", "success")

    all_suppliers = conn.execute(
        "SELECT id, nit, name, contact_name, phone FROM suppliers ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template("suppliers.html", suppliers=all_suppliers)

@suppliers_bp.route("/api/suppliers")
@login_required
def api_suppliers():
    conn = get_db_connection()
    suppliers_list = conn.execute(
        "SELECT nit, name, contact_name, phone FROM suppliers"
    ).fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in suppliers_list])

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from db import get_db_connection
from utils import login_required, role_required
import io
import csv
import sqlite3

products_bp = Blueprint('products', __name__)

@products_bp.route("/products", methods=("GET", "POST"))
@login_required
def products():
    if session.get("role") not in ["ADMIN", "COMPRAS", "ALMACEN"]:
        return redirect(url_for("reports.dashboard"))

    conn = get_db_connection()
    search = request.args.get("search")

    if request.method == "POST":
        action = request.form.get("action", "CREATE")

        if session.get("role") not in ["ADMIN", "ALMACEN"]:
            flash("Acceso denegado.", "error")
            return redirect(url_for("products.products"))

        code = request.form.get("code")
        description = request.form.get("description")
        unit_of_measure = request.form.get("unit_of_measure")

        if action == "CREATE":
            if not code or not description or not unit_of_measure:
                flash("Todos los campos son requeridos", "error")
            else:
                try:
                    conn.execute(
                        "INSERT INTO products (code, description, unit_of_measure) VALUES (?, ?, ?)",
                        (code, description, unit_of_measure),
                    )
                    conn.commit()
                    flash("Producto creado exitosamente.", "success")
                except sqlite3.IntegrityError:
                    flash(f"El código {code} ya existe.", "error")

        elif action == "UPDATE":
            conn.execute(
                "UPDATE products SET description=?, unit_of_measure=? WHERE code=?",
                (description, unit_of_measure, code),
            )
            conn.commit()
            flash("Producto actualizado.", "success")

        elif action == "DELETE":
            in_use = conn.execute(
                "SELECT 1 FROM maintenance_items WHERE product_code = ? LIMIT 1",
                (code,),
            ).fetchone()

            if in_use:
                flash("No se puede eliminar: el producto está en uso.", "error")
            else:
                conn.execute("DELETE FROM products WHERE code=?", (code,))
                conn.commit()
                flash("Producto eliminado correctamente.", "success")

    if search:
        all_products = conn.execute(
            "SELECT * FROM products WHERE description LIKE ? ORDER BY description ASC",
            (f"%{search}%",),
        ).fetchall()
    else:
        all_products = conn.execute(
            "SELECT * FROM products ORDER BY description ASC"
        ).fetchall()

    conn.close()
    return render_template("products.html", products=all_products, search=search)

@products_bp.route("/products/upload_csv", methods=("POST",))
@login_required
@role_required("ADMIN")
def upload_csv():
    if "csv_file" not in request.files:
        return redirect(url_for("products.products"))

    file = request.files["csv_file"]

    if file and file.filename.endswith(".csv"):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        conn = get_db_connection()
        current_codes = {
            row["code"] for row in conn.execute("SELECT code FROM products").fetchall()
        }

        add_c = 0
        next(csv_input, None)

        for row in csv_input:
            if len(row) >= 3:
                c, d, u = [x.strip() for x in row[:3]]
                if c not in current_codes and c:
                    try:
                        conn.execute(
                            "INSERT INTO products (code, description, unit_of_measure) VALUES (?, ?, ?)",
                            (c, d, u),
                        )
                        current_codes.add(c)
                        add_c += 1
                    except sqlite3.IntegrityError:
                        pass

        conn.commit()
        conn.close()
        flash(f"CSV importado. {add_c} productos agregados.", "success")

    return redirect(url_for("products.products"))

@products_bp.route("/api/products")
@login_required
def api_products():
    conn = get_db_connection()
    products_list = conn.execute(
        "SELECT code, description, unit_of_measure FROM products ORDER BY description ASC"
    ).fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in products_list])

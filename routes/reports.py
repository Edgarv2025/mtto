from flask import Blueprint, render_template
from db import get_db_connection
from utils import login_required, role_required

reports_bp = Blueprint('reports', __name__)

@reports_bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")

@reports_bp.route("/reports")
@login_required
@role_required("ADMIN")
def reports():
    conn = get_db_connection()

    status_data = conn.execute("""
        SELECT status, COUNT(*) as count 
        FROM maintenance_items 
        GROUP BY status
    """).fetchall()

    priority_data = conn.execute("""
        SELECT priority, COUNT(*) as count
        FROM maintenance_items
        GROUP BY priority
    """).fetchall()

    cost_data = conn.execute("""
    SELECT p.description as product_code, SUM(
        CASE 
            WHEN i.status = 'COMPRA_EN_CURSO' THEN COALESCE(i.v_tot1, 0)
            WHEN i.prov_compra = i.prov1 THEN COALESCE(i.v_tot1, 0)
            WHEN i.prov_compra = i.prov2 THEN COALESCE(i.v_tot2, 0)
            WHEN i.prov_compra = i.prov3 THEN COALESCE(i.v_tot3, 0)
            ELSE COALESCE(i.v_tot1, 0)
        END
    ) as total_cost
    FROM maintenance_items i
    LEFT JOIN products p ON i.product_code = p.code
    WHERE i.status IN ('COMPRA_EN_CURSO', 'TRANSITO', 'RECIBIDO')
    GROUP BY i.product_code
    ORDER BY total_cost DESC
    LIMIT 10
    """).fetchall()

    dest_cost_data = conn.execute("""
    SELECT r.destination, SUM(
        CASE 
            WHEN i.status = 'COMPRA_EN_CURSO' THEN COALESCE(i.v_tot1, 0)
            WHEN i.prov_compra = i.prov1 THEN COALESCE(i.v_tot1, 0)
            WHEN i.prov_compra = i.prov2 THEN COALESCE(i.v_tot2, 0)
            WHEN i.prov_compra = i.prov3 THEN COALESCE(i.v_tot3, 0)
            ELSE COALESCE(i.v_tot1, 0)
        END
    ) as total_cost
    FROM maintenance_items i
    JOIN maintenance_records r ON i.record_id = r.id
    WHERE i.status IN ('COMPRA_EN_CURSO', 'TRANSITO', 'RECIBIDO')
    GROUP BY r.destination
    ORDER BY total_cost DESC
    LIMIT 10
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        status_data=[dict(r) for r in status_data],
        priority_data=[dict(r) for r in priority_data],
        cost_data=[dict(r) for r in cost_data],
        dest_cost_data=[dict(r) for r in dest_cost_data]
    )

@reports_bp.route("/api/dashboard/hash")
@login_required
def dashboard_hash():
    conn = get_db_connection()
    res = conn.execute(
        "SELECT status, COUNT(*) FROM maintenance_items GROUP BY status"
    ).fetchall()
    conn.close()
    return "-".join([f"{r['status']}:{r[1]}" for r in res])

import os
from flask import request, redirect, url_for, flash, current_app

@reports_bp.route("/upload_logo", methods=["POST"])
@login_required
@role_required("ADMIN")
def upload_logo():
    file = request.files.get("logo")
    if file:
        filepath = os.path.join(current_app.root_path, "static", "images", "logo.png")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        flash("Logo actualizado exitosamente.", "success")
    return redirect(request.referrer or url_for("reports.dashboard"))

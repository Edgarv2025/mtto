from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from db import get_db_connection
from utils import login_required, role_required, notify_status_change
from datetime import datetime

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route("/maintenance", methods=("GET", "POST"))
@login_required
@role_required("ADMIN", "ALMACEN")
def maintenance():
    conn = get_db_connection()

    if request.method == "POST":
        date_str = request.form["date"]
        requested_by = request.form["requested_by"]
        storekeeper = request.form["storekeeper"]
        destination = request.form["destination"]

        cursor = conn.cursor()
        last_rec = cursor.execute(
            "SELECT MAX(consecutive_no) FROM maintenance_records"
        ).fetchone()
        next_c = 1 if last_rec[0] is None else last_rec[0] + 1

        cursor.execute(
            """INSERT INTO maintenance_records (consecutive_no, date, requested_by, storekeeper, destination)
                          VALUES (?, ?, ?, ?, ?)""",
            (next_c, date_str, requested_by, storekeeper, destination),
        )
        rec_id = cursor.lastrowid

        items_count = 0
        items_created_ids = []
        for i in range(1, 16):
            c = request.form.get(f"code_{i}")
            if c:
                q = request.form.get(f"quantity_{i}")
                q_val = float(q) if q else 1.0
                u = request.form.get(f"unit_{i}")
                o = request.form.get(f"obs_{i}")
                p = request.form.get(f"priority_{i}", "Media")
                cursor.execute(
                    """INSERT INTO maintenance_items (record_id, product_code, quantity, unit_of_measure, observaciones_solicitante, priority, status)
                                  VALUES (?, ?, ?, ?, ?, ?, 'PENDIENTE_JEFE')""",
                    (rec_id, c, q_val, u, o, p),
                )
                items_created_ids.append(cursor.lastrowid)
                items_count += 1

        conn.commit()
        conn.close()
        
        # NOTIFY STATUS CHANGE AL CREAR (Trigger)
        for item_id in items_created_ids:
            notify_status_change(item_id, "NUEVO REQUERIMIENTO (PENDIENTE_JEFE)")
            
        flash(
            f"Mantenimiento Registrado con éxito (# {next_c}) con {items_count} productos solicitados.",
            "success",
        )
        return redirect(url_for("maintenance.maintenance"))

    last_rec = conn.execute(
        "SELECT MAX(consecutive_no) FROM maintenance_records"
    ).fetchone()
    next_c = 1 if last_rec[0] is None else last_rec[0] + 1
    prods = conn.execute("SELECT code, description FROM products").fetchall()
    conn.close()

    return render_template(
        "maintenance.html",
        next_consecutive=next_c,
        today=datetime.now().strftime("%Y-%m-%d"),
        prods=prods,
    )

@maintenance_bp.route("/maintenance/list")
@login_required
def maintenance_list():
    conn = get_db_connection()
    records = conn.execute(
        "SELECT * FROM maintenance_records ORDER BY consecutive_no DESC"
    ).fetchall()
    conn.close()
    return render_template("maintenance_list.html", records=records)

@maintenance_bp.route("/maintenance/delete/<int:rec_id>", methods=["POST"])
@login_required
@role_required("ADMIN", "ALMACEN")
def delete_maintenance(rec_id):
    conn = get_db_connection()
    obs = request.form.get("observation", "Sin motivo")
    anular_text = f"[ANULADO: {obs}] "

    # Obtener los items asociados form notifications
    items = conn.execute("SELECT id FROM maintenance_items WHERE record_id = ?", (rec_id,)).fetchall()
    
    conn.execute(
        'UPDATE maintenance_items SET status = "ANULADO" WHERE record_id = ?', (rec_id,)
    )
    conn.execute(
        'UPDATE maintenance_records SET destination = ? || destination WHERE id = ? AND destination NOT LIKE "[ANULADO:%"',
        (anular_text, rec_id),
    )
    conn.commit()
    conn.close()
    
    # Notify deletion for every item inside request
    for it in items:
        notify_status_change(it["id"], "ANULADO")
        
    flash(f"Registro de requerimiento anulado por: {obs}", "success")
    return redirect(url_for("maintenance.maintenance_list"))

@maintenance_bp.route("/items", methods=("GET",))
@login_required
def items_dashboard():
    filter_status = request.args.get("status")
    priority_filter = request.args.get("priority")
    ref_filter = request.args.get("ref")

    conn = get_db_connection()
    query = """
    SELECT i.*, p.description, r.consecutive_no, r.date, r.requested_by, r.destination
    FROM maintenance_items i
    LEFT JOIN products p ON i.product_code = p.code
    JOIN maintenance_records r ON i.record_id = r.id
    WHERE 1=1
    """
    params = []

    if filter_status:
        query += " AND i.status = ?"
        params.append(filter_status)
    if priority_filter:
        query += " AND i.priority = ?"
        params.append(priority_filter)
    if ref_filter:
        query += " AND r.consecutive_no = ?"
        params.append(ref_filter)

    query += " ORDER BY r.consecutive_no DESC, i.id ASC"
    db_items = conn.execute(query, params).fetchall()
    conn.close()

    items = []
    for row in db_items:
        r_dict = dict(row)
        try:
            req_date = datetime.strptime(r_dict["date"], "%Y-%m-%d").date()
            r_dict["days_elapsed"] = (datetime.today().date() - req_date).days
        except Exception:
            r_dict["days_elapsed"] = 0
        items.append(r_dict)

    return render_template(
        "items_dashboard.html",
        items=items,
        current_filter=filter_status,
        priority_filter=priority_filter,
    )

@maintenance_bp.route("/update_item/<int:item_id>", methods=("POST",))
@login_required
def update_item(item_id):
    role = session.get("role")
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM maintenance_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return redirect(url_for("maintenance.items_dashboard"))

    status = item["status"]
    ns = None

    if role in ['JEFE_AREA', 'ADMIN'] and status == 'PENDIENTE_JEFE':
        decision = (request.form.get('decision_jefe') or request.args.get('decision_jefe') or '').strip().upper()
        
        # Fallback to check if it's sent as action
        if not decision:
            if 'decision_jefe=SI' in request.get_data(as_text=True): decision = 'SI'
            elif 'decision_jefe=NO' in request.get_data(as_text=True): decision = 'NO'
            
        obs = request.form.get('obs_jefe', '')
        
        if decision == 'SI':
            ns = 'COTIZACION'
        elif decision == 'NO':
            ns = 'RECHAZADO'
        else:
            flash("Debe seleccionar Aprobar o Rechazar.", "error")
            return redirect(url_for("maintenance.items_dashboard"))

        conn.execute('UPDATE maintenance_items SET aprobado_jefe=?, observaciones_jefe=?, status=? WHERE id=?',
                     (True if decision == 'SI' else False, obs, ns, item_id))

    elif role in ['GT', 'ADMIN'] and status == 'PENDIENTE_GT':
        decision = (request.form.get('decision_gt') or '').strip().upper()
        if not decision:
            if 'decision_gt=SI' in request.get_data(as_text=True): decision = 'SI'
            elif 'decision_gt=NO' in request.get_data(as_text=True): decision = 'NO'
            
        obs = request.form.get('obs_gt', '')
        
        if decision == 'SI':
            ns = 'PENDIENTE_GR'
        elif decision == 'NO':
            ns = 'RECHAZADO'
        else:
            flash("Debe seleccionar Aprobar o Rechazar.", "error")
            return redirect(url_for("maintenance.items_dashboard"))
            
        conn.execute('UPDATE maintenance_items SET aprobado_gt=?, observaciones_gt=?, status=? WHERE id=?',
                     (True if decision == 'SI' else False, obs, ns, item_id))

    elif role in ['COMPRAS', 'ADMIN']:
        action = request.form.get('action')
        if action == 'COTIZAR' and status == 'COTIZACION':
            c1p, c1v = request.form.get('c1p'), request.form.get('c1v')
            c2p, c2v = request.form.get('c2p'), request.form.get('c2v')
            c3p, c3v = request.form.get('c3p'), request.form.get('c3v')
            c1t, c2t, c3t = request.form.get('c1t'), request.form.get('c2t'), request.form.get('c3t')
            ns = 'PENDIENTE_GT'
            conn.execute('''UPDATE maintenance_items 
                            SET prov1=?, v_unit1=?, v_tot1=?, 
                                prov2=?, v_unit2=?, v_tot2=?, 
                                prov3=?, v_unit3=?, v_tot3=?, status=? 
                            WHERE id=?''', (c1p, c1v, c1t, c2p, c2v, c2t, c3p, c3v, c3t, ns, item_id))
                            
        elif action == 'COMPRAR' and status == 'COMPRA_EN_CURSO':
            fc = request.form.get('fecha_compra')
            pc = request.form.get('prov_compra')
            oc = request.form.get('orden_compra')
            ns = 'TRANSITO'
            conn.execute('UPDATE maintenance_items SET fecha_compra=?, prov_compra=?, orden_compra=?, status=? WHERE id=?',
                         (fc, pc, oc, ns, item_id))
                         
    elif role in ['GR', 'ADMIN'] and status == 'PENDIENTE_GR':
        decision = (request.form.get('decision_gr') or '').strip().upper()
        if not decision:
            if 'decision_gr=SI' in request.get_data(as_text=True): decision = 'SI'
            elif 'decision_gr=NO' in request.get_data(as_text=True): decision = 'NO'
            
        obs = request.form.get('obs_gr', '')
        
        if decision == 'SI':
            ns = 'COMPRA_EN_CURSO'
        elif decision == 'NO':
            ns = 'RECHAZADO'
        else:
            flash("Debe seleccionar Aprobar o Rechazar.", "error")
            return redirect(url_for("maintenance.items_dashboard"))
            
        conn.execute('UPDATE maintenance_items SET aprobado_gr=?, observaciones_gr=?, status=? WHERE id=?',
                     (True if decision == 'SI' else False, obs, ns, item_id))

    elif role in ['ALMACEN', 'ADMIN'] and status == 'TRANSITO':
        fl, cl = request.form.get('fecha_llegada'), request.form.get('cant_llegada')
        obs_rec = request.form.get('obs_recepcion', '')
        ns = 'RECIBIDO'
        conn.execute('UPDATE maintenance_items SET fecha_llegada=?, cant_llegada=?, observaciones_recepcion=?, status=? WHERE id=?',
                     (fl, cl, obs_rec, ns, item_id))

    conn.commit()
    conn.close()
    
    # ENVIAR CORREO TRAS EL CAMBIO DE FASE
    if ns:
        notify_status_change(item_id, ns)
    
    flash(f'Ítem actualizado correctamente.', 'success')
    if ns:
        return redirect(url_for('maintenance.items_dashboard', status=ns))
    return redirect(url_for('maintenance.items_dashboard'))

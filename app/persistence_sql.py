# ======================================================
# SEAC v1.4 — Persistencia en SQL Server (sesiones, feedback, productos y pesos)
# ======================================================
from typing import Dict, List, Any
from .db import get_conn

# ------------------------------------------------------
# Sesiones
# ------------------------------------------------------
def add_session(session_id: str, uso: str, presupuesto: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    IF NOT EXISTS (SELECT 1 FROM sessions WHERE session_id=?)
        INSERT INTO sessions (session_id, uso, presupuesto) VALUES (?, ?, ?)
    ELSE
        UPDATE sessions SET uso=?, presupuesto=? WHERE session_id=?;
    """, (session_id, session_id, uso, presupuesto, uso, presupuesto, session_id))
    conn.close()

# ------------------------------------------------------
# Feedback (versión final - evita duplicados por nombre)
# ------------------------------------------------------
def add_feedback(session_id: str, product_or_id, uso: str, rating: float):
    conn = get_conn()
    cur = conn.cursor()

    # --- Si llega solo el id (string) ---
    if isinstance(product_or_id, str):
        pid = product_or_id.strip()

        # Intentar obtener nombre real si es un ID tipo "groq-..."
        if pid.startswith("groq-"):
            # Buscar un producto similar existente (por nombre parcial del ID)
            cur.execute("""
                SELECT TOP 1 id, name, brand FROM products
                WHERE name LIKE ? OR id LIKE ?;
            """, (f"%{pid[-5:]}%", f"%{pid[-5:]}%"))
            row = cur.fetchone()

            if row:
                real_id = row[0]
                name = row[1]
                brand = row[2]
                print(f"🔁 Producto similar encontrado → {brand} {name} ({real_id})")
            else:
                # No existe → crear placeholder temporal
                cur.execute("""
                    INSERT INTO products (id, name, brand, category, cpu, gpu, ram, storage, os, price, url)
                    VALUES (?, ?, 'Desconocido', 'Laptop', '', '', '', '', '', 0, '');
                """, (pid, f"Producto_{pid}"))
                conn.commit()
                real_id = pid
                name = f"Producto_{pid}"
                brand = "Desconocido"
                print(f"🆕 Placeholder creado → {name}")
        else:
            # Buscar producto normal por ID exacto
            cur.execute("SELECT TOP 1 id, name, brand FROM products WHERE id=?", (pid,))
            row = cur.fetchone()
            if row:
                real_id, name, brand = row
            else:
                cur.execute("""
                    INSERT INTO products (id, name, brand, category, cpu, gpu, ram, storage, os, price, url)
                    VALUES (?, ?, 'Desconocido', 'Laptop', '', '', '', '', '', 0, '');
                """, (pid, f"Producto_{pid}"))
                conn.commit()
                real_id = pid
                name = f"Producto_{pid}"
                brand = "Desconocido"

    # --- Si llega un diccionario completo ---
    elif isinstance(product_or_id, dict):
        p = product_or_id
        name = (p.get("name") or p.get("modelo") or "").strip()
        brand = (p.get("brand") or p.get("marca") or "Desconocido").strip()
        category = p.get("category", "Laptop")
        cpu = p.get("cpu", "") or p.get("procesador", "")
        gpu = p.get("gpu", "") or p.get("tarjeta_grafica", "")
        ram = p.get("ram", "") or p.get("memoria_ram", "")
        storage = p.get("storage", "") or p.get("almacenamiento", "")
        osys = p.get("os", "") or p.get("sistema_operativo", "")
        price = float(p.get("price", p.get("precio", 0)) or 0.0)
        url = p.get("url", "") or p.get("link", "")

        # Buscar si ya existe un producto con el mismo nombre y marca
        cur.execute("""
            SELECT TOP 1 id FROM products
            WHERE LOWER(name)=LOWER(?) AND LOWER(brand)=LOWER(?)
        """, (name, brand))
        row = cur.fetchone()

        if not row:
            real_id = f"auto-{brand[:3]}-{name[:6]}".replace(" ", "").lower()
            cur.execute("""
                INSERT INTO products (id, name, brand, category, cpu, gpu, ram, storage, os, price, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (real_id, name, brand, category, cpu, gpu, ram, storage, osys, price, url))
            conn.commit()
            print(f"🆕 Producto nuevo insertado → {brand} {name} ({real_id})")
        else:
            real_id = row[0]
            cur.execute("""
                UPDATE products SET
                    brand = CASE WHEN brand='Desconocido' THEN ? ELSE brand END,
                    cpu = CASE WHEN cpu='' OR cpu IS NULL THEN ? ELSE cpu END,
                    gpu = CASE WHEN gpu='' OR gpu IS NULL THEN ? ELSE gpu END,
                    ram = CASE WHEN ram='' OR ram IS NULL THEN ? ELSE ram END,
                    storage = CASE WHEN storage='' OR storage IS NULL THEN ? ELSE storage END,
                    os = CASE WHEN os='' OR os IS NULL THEN ? ELSE os END,
                    price = CASE WHEN price=0 THEN ? ELSE price END,
                    url = CASE WHEN url='' OR url IS NULL THEN ? ELSE url END
                WHERE id=?;
            """, (brand, cpu, gpu, ram, storage, osys, price, url, real_id))
            conn.commit()
            print(f"♻️ Producto actualizado → {brand} {name} ({real_id})")

    else:
        print("❌ add_feedback recibió un tipo no válido.")
        conn.close()
        return

    # --- Insertar feedback ---
    cur.execute("""
        INSERT INTO feedback (session_id, product_id, uso, rating)
        VALUES (?, ?, ?, ?);
    """, (session_id, real_id, uso, rating))
    conn.commit()
    conn.close()
    print(f"⭐ Feedback registrado para {brand} {name}")

# ------------------------------------------------------
# Historial de feedback + sesiones
# ------------------------------------------------------
def load_history() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT f.session_id, f.product_id, f.uso, f.rating, f.ts, s.presupuesto
    FROM feedback f
    LEFT JOIN sessions s ON s.session_id = f.session_id
    ORDER BY f.id DESC;
    """)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows

# ------------------------------------------------------
# Pesos de aprendizaje
# ------------------------------------------------------
def load_weights() -> Dict[str, Dict[str, float]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uso, w_presupuesto, w_uso, w_marca FROM weights;")
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    conn.close()
    out: Dict[str, Dict[str, float]] = {}
    for r in rows:
        d = dict(zip(cols, r))
        out[d["uso"]] = {
            "presupuesto": float(d["w_presupuesto"] or 1.0),
            "uso": float(d["w_uso"] or 1.0),
            "preferencia_marca": float(d["w_marca"] or 0.3),
        }
    return out

def save_weights(weights: Dict[str, Dict[str, float]]):
    conn = get_conn()
    cur = conn.cursor()
    for uso, w in weights.items():
        cur.execute("""
        IF EXISTS (SELECT 1 FROM weights WHERE uso=?)
            UPDATE weights SET w_presupuesto=?, w_uso=?, w_marca=? WHERE uso=?;
        ELSE
            INSERT INTO weights (uso, w_presupuesto, w_uso, w_marca)
            VALUES (?, ?, ?, ?);
        """, (uso, w.get("presupuesto",1.0), w.get("uso",1.0), w.get("preferencia_marca",0.3),
              uso, uso, w.get("presupuesto",1.0), w.get("uso",1.0), w.get("preferencia_marca",0.3)))
    conn.close()

# ------------------------------------------------------
# Productos (upsert inteligente mejorado)
# ------------------------------------------------------
def add_or_update_product(p: Dict[str, Any]):
    """
    Inserta o actualiza un producto. Si ya existe un placeholder
    (creado automáticamente) lo rellena con los datos reales.
    """
    if not p:
        return

    pid = p.get("id", "")
    name = p.get("name", "") or p.get("modelo", "")
    brand = p.get("brand", "") or p.get("marca", "")
    category = p.get("category", "Laptop")
    cpu = p.get("cpu", "") or p.get("procesador", "")
    gpu = p.get("gpu", "") or p.get("tarjeta_grafica", "")
    ram = p.get("ram", "") or p.get("memoria_ram", "")
    storage = p.get("storage", "") or p.get("almacenamiento", "")
    osys = p.get("os", "") or p.get("sistema_operativo", "")
    price = float(p.get("price", p.get("precio", 0)) or 0)
    url = p.get("url", "") or p.get("link", "")

    conn = get_conn()
    cur = conn.cursor()

    # Buscar si ya existe por ID o por nombre+marca
    cur.execute("""
        SELECT TOP 1 id FROM products
        WHERE id=? OR (LOWER(name)=LOWER(?) AND LOWER(brand)=LOWER(?))
    """, (pid, name, brand))
    row = cur.fetchone()

    if not row:
        # No existe → crear nuevo
        cur.execute("""
            INSERT INTO products (id, name, brand, category, cpu, gpu, ram, storage, os, price, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, name, brand, category, cpu, gpu, ram, storage, osys, price, url))
        conn.commit()
        print(f"🆕 Producto insertado → {brand} {name}")
    else:
        # Existe → actualizar datos vacíos o placeholder
        real_id = row[0]
        cur.execute("""
            UPDATE products SET
                name = CASE WHEN (name IS NULL OR name LIKE 'Producto_%') THEN ? ELSE name END,
                brand = CASE WHEN (brand IS NULL OR brand='Desconocido') THEN ? ELSE brand END,
                category = ?,
                cpu = CASE WHEN (cpu IS NULL OR cpu='') THEN ? ELSE cpu END,
                gpu = CASE WHEN (gpu IS NULL OR gpu='') THEN ? ELSE gpu END,
                ram = CASE WHEN (ram IS NULL OR ram='') THEN ? ELSE ram END,
                storage = CASE WHEN (storage IS NULL OR storage='') THEN ? ELSE storage END,
                os = CASE WHEN (os IS NULL OR os='') THEN ? ELSE os END,
                price = CASE WHEN (price IS NULL OR price=0) THEN ? ELSE price END,
                url = CASE WHEN (url IS NULL OR url='') THEN ? ELSE url END
            WHERE id = ?;
        """, (name, brand, category, cpu, gpu, ram, storage, osys, price, url, real_id))
        conn.commit()
        print(f"♻️ Producto actualizado → {brand} {name}")

    conn.close()
# ===============================================
# FastAPI — SEAC v1.4 (con caché temporal y feedback selectivo)
# ===============================================
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()

from .schemas import Consulta, Recomendacion, Feedback, Producto
from .inference_net import infer_hibrido
from .persistence_sql import add_session
from .learning import load_weights, save_weights, update_weights_from_feedback
from .users_controller import router as users_router

from .db import get_conn


# ===================== APP =====================
app = FastAPI(title="SEAC — Sistema Experto Asistente de Compras", version="1.4")

if os.path.isdir("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# ===================== CACHE DE PRODUCTOS =====================
cache_productos = {}  # Almacena productos de la última inferencia


# ===================== FRONTEND =====================
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("bienvenida.html", {"request": request})

@app.get("/index", response_class=HTMLResponse)
def ui_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ===================== BACKEND =====================
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.4"}

@app.get("/version")
def version():
    return {"app": "SEAC — Sistema Experto Asistente de Compras", "version": "1.4"}


# -------- Normalizador de productos --------
def _normalize_product_dict(prod_dict: dict) -> dict:
    """Convierte claves en español o inglés al formato estándar y asegura que todos los campos existan."""
    def pick(*keys, default=""):
        for k in keys:
            if k in prod_dict and prod_dict[k] not in (None, ""):
                return prod_dict[k]
        return default

    # Precio robusto
    raw_price = pick("price", "precio", default=0)
    if isinstance(raw_price, str):
        try:
            raw_price = float(raw_price.replace("$", "").replace(",", "").strip())
        except Exception:
            raw_price = 0.0
    elif not isinstance(raw_price, (int, float)):
        raw_price = 0.0

    normalized = {
        "id": pick("id", default=""),
        "name": pick("name", "modelo", default=""),
        "brand": pick("brand", "marca", default=""),
        "category": pick("category", default="Laptop"),
        "cpu": pick("cpu", "procesador", default=""),
        "gpu": pick("gpu", "tarjeta_grafica", default=""),
        "ram": pick("ram", "memoria_ram", default=""),
        "storage": pick("storage", "almacenamiento", default=""),
        "os": pick("os", "sistema_operativo", default=""),
        "price": float(raw_price),
        "url": pick("url", "link", default=""),
    }
    return normalized


# -------- Descripción formal --------
def _descripcion_formal(prod: dict, uso: str) -> str:
    """Construye una descripción profesional con todos los campos."""
    nombre = f"{prod.get('brand', '')} {prod.get('name', '')}".strip()
    cuerpo = (
        f"Procesador: {prod.get('cpu', 'N/D')}; "
        f"Memoria RAM: {prod.get('ram', 'N/D')}; "
        f"Almacenamiento: {prod.get('storage', 'N/D')}; "
        f"Tarjeta gráfica: {prod.get('gpu', 'N/D')}; "
        f"Sistema operativo: {prod.get('os', 'N/D')}; "
        f"Precio: ${prod.get('price', 0):.2f}"
    )
    cierre = f"Recomendado para uso {uso}." if uso else "Recomendado según los requerimientos."
    return f"{nombre} — {cuerpo}. {cierre}"


# -------- Endpoint principal /infer --------
@app.post("/infer", response_model=List[Recomendacion])
def inferir(consulta: Consulta):
    try:
        from .persistence_sql import add_or_update_product

        resultados = infer_hibrido(consulta.model_dump())
        if not resultados:
            return []

        out = []
        session_id = resultados[0].get("session_id")
        if session_id:
            add_session(session_id, consulta.uso, consulta.presupuesto)

        global cache_productos
        cache_productos.clear()  # limpiar la caché anterior

        for item in resultados:
            prod_dict = item.get("product", {})
            prod_norm = _normalize_product_dict(prod_dict)

            # Guardar producto temporalmente en caché
            if prod_norm.get("id"):
                cache_productos[prod_norm["id"]] = prod_norm

            prod = Producto(**prod_norm)
            descripcion = _descripcion_formal(prod_norm, consulta.uso)
            reasons = item.get("reasons", []) + [descripcion]
            out.append({
                "product": prod.model_dump(),
                "score": item.get("score", 0),
                "reasons": reasons,
                "session_id": session_id
            })

        print(f"[CACHE] {len(cache_productos)} productos guardados temporalmente.")
        return out

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en /infer: {e}")

app.include_router(users_router)

# -------- Endpoint /feedback --------
@app.post("/feedback")
def feedback(fb: Feedback):
    try:
        from .learning import add_feedback_entry
        conn = get_conn()
        cur = conn.cursor()

        # 🟢 Buscar producto por nombre + marca
        cur.execute("""
            SELECT TOP 1 * FROM products
            WHERE LOWER(name)=LOWER(?) AND LOWER(brand)=LOWER(?)
        """, (fb.product_name, fb.brand or ""))
        row = cur.fetchone()

        producto = None
        if row:
            cols = [c[0] for c in cur.description]
            producto = dict(zip(cols, row))
            print(f"✅ Producto encontrado → {fb.brand} {fb.product_name}")

            # 🧩 Actualizar campos vacíos con nuevos datos
            update_fields = {}
            for field in ["cpu", "gpu", "ram", "storage", "os", "price"]:
                valor_nuevo = getattr(fb, field, None)
                if (not producto.get(field)) and valor_nuevo:
                    update_fields[field] = valor_nuevo

            if update_fields:
                sets = ", ".join([f"{k}=?" for k in update_fields])
                params = list(update_fields.values()) + [producto["id"]]
                cur.execute(f"UPDATE products SET {sets} WHERE id=?", params)
                conn.commit()
                print(f"♻️ Producto actualizado → {fb.brand} {fb.product_name}")

        # 🟠 Si no existe, crear producto completo
        if not producto:
            new_id = f"auto-{(fb.brand or 'unk')[:3]}-{(fb.product_name or 'prod')[:5]}".replace(" ", "").lower()
            cur.execute("""
                INSERT INTO products (id, name, brand, category, cpu, gpu, ram, storage, os, price, url)
                VALUES (?, ?, ?, 'Laptop', ?, ?, ?, ?, ?, ?, '');
            """, (
                new_id,
                fb.product_name or "Desconocido",
                fb.brand or "(desconocida)",
                getattr(fb, "cpu", ""),
                getattr(fb, "gpu", ""),
                getattr(fb, "ram", ""),
                getattr(fb, "storage", ""),
                getattr(fb, "os", ""),
                getattr(fb, "price", 0.0)
            ))
            conn.commit()
            producto = {
                "id": new_id,
                "name": fb.product_name,
                "brand": fb.brand,
                "cpu": getattr(fb, "cpu", ""),
                "gpu": getattr(fb, "gpu", ""),
                "ram": getattr(fb, "ram", ""),
                "storage": getattr(fb, "storage", ""),
                "os": getattr(fb, "os", ""),
                "price": getattr(fb, "price", 0.0)
            }
            print(f"🆕 Producto creado → {producto['brand']} {producto['name']}")

        # 💾 Guardar feedback en tabla feedback
        add_feedback_entry(fb.session_id, producto, fb.notes or "default", fb.rating)

        # ⭐ Agregar a favoritos solo si el usuario existe y no está repetido
        if fb.rating >= 0.8 and fb.user_id:
            cur.execute("""
                SELECT TOP 1 f.product_id
                FROM favorites f
                JOIN products p ON p.id = f.product_id
                WHERE f.user_id = ? AND LOWER(p.name)=LOWER(?) AND LOWER(p.brand)=LOWER(?)
            """, (fb.user_id, producto["name"], producto["brand"]))
            exists = cur.fetchone()

            if exists:
                print(f"⚠️ El usuario {fb.user_id} ya tenía este producto en favoritos ({producto['name']}).")
            else:
                cur.execute("""
                    INSERT INTO favorites (user_id, product_id)
                    VALUES (?, ?);
                """, (fb.user_id, producto["id"]))
                print(f"⭐ Producto agregado a favoritos → {producto['name']}")
            conn.commit()

        # 🧠 Aprendizaje adaptativo
        weights = load_weights()
        uso = fb.notes or "default"
        new_w = update_weights_from_feedback(weights, uso, fb.rating)
        save_weights(new_w)

        conn.close()
        return {
            "ok": True,
            "uso": uso,
            "rating": fb.rating,
            "producto_guardado": producto["name"],
            "weights": new_w.get(uso, {})
        }

    except Exception as e:
        import traceback
        print("❌ Error interno en /feedback:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
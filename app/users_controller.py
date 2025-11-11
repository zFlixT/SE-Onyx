from fastapi import APIRouter, HTTPException
from .db import get_conn
import hashlib

router = APIRouter(prefix="/users", tags=["Usuarios"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/register")
def register(email: str, password: str, first_name: str = "", last_name: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM users WHERE email=?", (email,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="El usuario ya existe.")

    hashed = hash_password(password)
    cur.execute("""
        INSERT INTO users (email, password, first_name, last_name)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?);
    """, (email, hashed, first_name.strip(), last_name.strip()))
    row = cur.fetchone()
    conn.close()

    return {
        "ok": True,
        "msg": "Usuario registrado correctamente.",
        "user_id": row[0],
        "email": email,
        "first_name": first_name.strip(),
        "last_name": last_name.strip()
    }

@router.post("/login")
def login(email: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password, first_name, last_name, email FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if row[1] != hash_password(password):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    return {
        "ok": True,
        "msg": "Inicio de sesión exitoso.",
        "user_id": row[0],
        "first_name": row[2] or "",
        "last_name": row[3] or "",
        "email": row[4]
    }

@router.get("/{user_id}/favorites")
def get_favorites(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT p.id, p.name, p.brand, p.category, p.cpu, p.gpu, p.ram, p.storage, p.os, p.price, p.url, f.added_at
    FROM favorites f
    JOIN products p ON p.id = f.product_id
    WHERE f.user_id = ?
    ORDER BY f.added_at DESC;
    """, (user_id,))
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return {"ok": True, "favorites": rows, "total": len(rows)}

@router.delete("/{user_id}/favorites/{product_id}")
def remove_favorite(user_id: int, product_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM favorites WHERE user_id=? AND product_id=?;", (user_id, product_id))
    conn.close()
    return {"ok": True, "msg": f"Producto {product_id} eliminado de favoritos del usuario {user_id}."}
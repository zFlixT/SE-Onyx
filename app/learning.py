# ======================================================
# SEAC v1.4 — Lógica de aprendizaje y retroalimentación
# ======================================================
from typing import Dict
from .persistence_sql import (
    add_feedback as _add_feedback_db,
    load_weights as _load_w_db,
    save_weights as _save_w_db,
    add_or_update_product
)
from .db import get_conn

# Pesos base por defecto
DEFAULT_TEMPLATE = {
    "presupuesto": 1.0,
    "uso": 1.0,
    "preferencia_marca": 0.3
}

# ------------------------------------------------------
# Cargar pesos
# ------------------------------------------------------
def load_weights() -> Dict[str, Dict[str, float]]:
    w = _load_w_db()
    if not w or "default" not in w:
        w = {"default": DEFAULT_TEMPLATE.copy(), **w}
        _save_w_db(w)
    return w

# ------------------------------------------------------
# Guardar pesos
# ------------------------------------------------------
def save_weights(w: Dict[str, Dict[str, float]]):
    for uso, block in w.items():
        for k, v in block.items():
            block[k] = float(round(v, 3))
    _save_w_db(w)

# ------------------------------------------------------
# Actualizar pesos según feedback
# ------------------------------------------------------
def update_weights_from_feedback(weights: Dict[str, Dict[str, float]], uso: str, rating: float, lr: float = 0.05) -> Dict[str, Dict[str, float]]:
    if uso not in weights:
        weights[uso] = DEFAULT_TEMPLATE.copy()

    adjust = (rating - 0.5) * 2.0
    for k in DEFAULT_TEMPLATE.keys():
        weights[uso][k] = max(0.05, min(2.5, weights[uso].get(k, 1.0) + lr * adjust))
        weights[uso][k] = float(round(weights[uso][k], 3))

    return weights

# ------------------------------------------------------
# Guardar feedback con creación automática de sesión
# ------------------------------------------------------
def add_feedback_entry(session_id: str, product: dict, uso: str, rating: float):
    """
    Registra feedback y crea la sesión si no existe.
    Solo guarda el producto si el usuario dio 'me gusta' (rating >= 0.8)
    """
    from .persistence_sql import add_feedback as _add_feedback_db, add_or_update_product
    from .db import get_conn

    # Crear sesión si no existe (para evitar FK)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    IF NOT EXISTS (SELECT 1 FROM sessions WHERE session_id=?)
        INSERT INTO sessions (session_id, uso, presupuesto) VALUES (?, ?, 0);
    """, (session_id, session_id, uso))
    conn.close()

    # Solo guardar el producto si el rating es alto (me gusta)
    if rating >= 0.8:
        add_or_update_product(product)

    # Registrar feedback siempre
    _add_feedback_db(session_id, product.get("id", ""), uso, rating)
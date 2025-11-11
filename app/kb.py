# =====================================================
# SEAC v1.3 — Carga de productos desde SQL Server
# =====================================================
from typing import List, Dict, Any
from .db import get_conn

def load_products() -> List[Dict[str, Any]]:
    """
    Carga los productos directamente desde la base de datos SQL Server.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, brand, category, cpu, gpu, ram, storage, os, price, url FROM products;")
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows

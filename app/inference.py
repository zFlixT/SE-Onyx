from typing import List, Dict, Any, Tuple
import uuid
from .rules import USO_MIN_REQ, BASE_WEIGHTS, gama_to_price_range, soft_threshold
from .learning import load_weights
from .kb import load_products
from .cbr import calcular_similitud

def score_candidate(p: Dict[str, Any], q: Dict[str, Any], weights: Dict[str, float]) -> Tuple[float, list[str]]:
    uso = q.get("uso")
    presupuesto = q.get("presupuesto")
    prefs = q.get("preferencias") or {}
    reasons: list[str] = []

    # Presupuesto
    if p["price"] <= presupuesto:
        budget_score = 1.0
        reasons.append(f"Precio dentro del presupuesto (${p['price']:.0f} ≤ ${presupuesto:.0f})")
    else:
        over = p["price"] - presupuesto
        budget_score = max(0.0, 1.0 - over / max(1.0, 0.25 * presupuesto))
        reasons.append(f"Precio sobre el presupuesto (+${over:.0f})")

    # Requisitos por uso
    min_req = USO_MIN_REQ.get(uso, {})
    uso_components = []
    uso_score_acc = 0.0
    count = 0
    for k, vmin in min_req.items():
        val = p.get(k, 0)
        s = soft_threshold(val, vmin)
        uso_score_acc += s
        count += 1
        uso_components.append((k, val, vmin, s))
    uso_score = uso_score_acc / count if count else 1.0
    for k, val, vmin, s in uso_components:
        if s >= 1.0:
            reasons.append(f"{k} cumple (valor={val} ≥ mín={vmin})")
        elif s == 0.0:
            reasons.append(f"{k} insuficiente (valor={val} < 0.8×mín={int(0.8*vmin)})")
        else:
            reasons.append(f"{k} cercano al mínimo (valor={val}, mín={vmin})")

    # Preferencia de marca
    if prefs.get("marca"):
        if p.get("brand","").lower() == prefs["marca"].lower():
            reasons.append(f"Marca preferida ({prefs['marca']})")

    # Pesos
    w_pres = weights.get("presupuesto", BASE_WEIGHTS["presupuesto"])
    w_uso  = weights.get("uso", BASE_WEIGHTS["uso"])
    w_marca= weights.get("preferencia_marca", BASE_WEIGHTS["preferencia_marca"])

    comp = (
        w_pres * budget_score +
        w_uso  * uso_score +
        w_marca* (1.05 if prefs.get('marca') and p.get('brand','').lower()==prefs['marca'].lower() else 1.0)
    ) / (w_pres + w_uso + w_marca)

    return float(comp), reasons

def infer(query: Dict[str, Any]) -> List[Dict[str, Any]]:
    products = load_products()
    weights = load_weights()
    gama = (query.get("gama") or "").lower().strip()
    if gama in ["baja","media","alta"]:
        lo, hi = gama_to_price_range(gama)
        candidates = [p for p in products if lo <= p["price"] <= hi]
        if not candidates:
            candidates = products
    else:
        candidates = products

    sim_cbr = calcular_similitud(query)
    scored = []
    for p in candidates:
        s, reasons = score_candidate(p, query, weights)
        score_total = (s * 0.8) + (sim_cbr * 0.2)
        reasons.append(f"Ajuste CBR (+{round(sim_cbr*100)}% de similitud con casos previos)")
        scored.append({"product": p, "score": round(float(score_total), 4), "reasons": reasons})

    scored.sort(key=lambda x: x["score"], reverse=True)
    session_id = str(uuid.uuid4())
    for item in scored:
        item["session_id"] = session_id
    k = max(1, min(int(query.get("top_k", 3)), 10))
    return scored[:k]

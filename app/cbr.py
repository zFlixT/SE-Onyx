from typing import Dict, Any, List
from .persistence_sql import load_history

def calcular_similitud(query: Dict[str, Any]) -> float:
    hist = load_history()
    if not hist:
        return 0.0

    uso_actual = query.get("uso", "default")
    presupuesto_nuevo = float(query.get("presupuesto", 0) or 0.0)
    similares: List[float] = []

    for h in hist:
        if h.get("uso") == uso_actual and float(h.get("rating",0)) >= 0.8:
            pres_ant = float(h.get("presupuesto") or 0.0)
            if pres_ant > 0 and presupuesto_nuevo > 0:
                sim = 1 - abs(presupuesto_nuevo - pres_ant) / pres_ant
                sim = max(0.0, min(1.0, sim))
                similares.append(sim)

    if not similares:
        return 0.0
    return round(sum(similares) / len(similares), 3)
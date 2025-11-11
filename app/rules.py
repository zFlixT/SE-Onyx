from typing import Dict, Tuple

# Reglas mínimas por uso
USO_MIN_REQ = {
    "gaming":        {"gpu_score": 60, "ram_gb": 16, "cpu_score": 65},
    "edicion":       {"cpu_score": 70, "ram_gb": 16, "storage_gb": 512},
    "oficina":       {"cpu_score": 45, "ram_gb": 8},
    "programacion":  {"cpu_score": 60, "ram_gb": 16},
    "movilidad":     {"ram_gb": 8},
    "diseno":        {"gpu_score": 60, "ram_gb": 16, "cpu_score": 70}
}

# Pesos base
BASE_WEIGHTS = {
    "presupuesto": 1.0,
    "uso": 1.0,
    "preferencia_marca": 0.3
}

def gama_to_price_range(gama: str) -> Tuple[float, float]:
    if gama == "baja": return (300, 700)
    if gama == "media": return (700, 1200)
    if gama == "alta": return (1200, 3000)
    return (0, 999999)

def soft_threshold(value: float, min_required: float) -> float:
    if min_required <= 0: return 1.0
    if value < 0.8 * min_required: return 0.0
    if value >= min_required: return 1.0
    return (value - 0.8 * min_required) / (0.2 * min_required)

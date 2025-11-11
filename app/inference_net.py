# =========================================================
# SEAC v1.6 — Motor híbrido con “Ajuste automático” + explicaciones
# =========================================================
from .api_internet import fetch_products_from_internet
from .kb import load_products
from .connectors.llm_groq import summarize_reasons_groq  # usa tu helper actual
import uuid

def infer_hibrido(consulta: dict):
    """Motor híbrido SEAC — usa Groq si hay conexión, KB local si no.
       Ahora devuelve (si aplica) una tarjeta informativa de 'Ajuste automático'."""
    uso = (consulta.get("uso") or "").strip()
    presupuesto = float(consulta.get("presupuesto", 0) or 0)
    preferencias = consulta.get("preferencias", {}) or {}
    top_k = int(consulta.get("top_k", 3) or 3)

    # Para explicar los cambios
    session_id = str(uuid.uuid4())
    uso_lower = uso.lower()
    presupuesto_original = presupuesto
    gama_original = (consulta.get("gama") or "").strip().lower()
    gama_anterior = gama_original  # para reportar si cambia
    ajustes_info = None

    # --- Ajuste inteligente (presupuesto + posible cambio de gama) ---
    # Reglas simples por tipo de uso:
    if "juego" in uso_lower or "gaming" in uso_lower:
        if presupuesto < 500:
            presupuesto = 700
            if gama_original in ("", "baja"):
                consulta["gama"] = "media"
    elif any(w in uso_lower for w in ["edicion", "diseño", "render", "arquitectura"]):
        if presupuesto < 400:
            presupuesto = 600
            if gama_original in ("", "baja"):
                consulta["gama"] = "media"
    elif any(w in uso_lower for w in ["program", "dev", "codigo", "programación"]):
        if presupuesto < 350:
            presupuesto = 500
            if gama_original in ("", "baja"):
                consulta["gama"] = "media"
    elif any(w in uso_lower for w in ["oficina", "trabajo", "estudio", "universidad"]):
        if presupuesto < 250:
            presupuesto = 400
            if gama_original == "":
                consulta["gama"] = "baja"
    else:
        # Caso básico: mínimos funcionales
        if presupuesto < 180:
            presupuesto = 250
            if gama_original == "":
                consulta["gama"] = "baja"

    gama_nueva = (consulta.get("gama") or "").strip().lower()

    # Construcción del mensaje de ajustes (si hubo)
    cambios = []
    if presupuesto != presupuesto_original:
        cambios.append(f"presupuesto de ${int(presupuesto_original)} a ${int(presupuesto)}")
    if gama_nueva and gama_nueva != gama_anterior:
        cambios.append(f"gama de '{gama_anterior or 'no especificada'}' a '{gama_nueva}'")

    if cambios:
        ajustes_info = "💡 Se aplicó un ajuste automático: " + " y ".join(cambios) + "."

    # --- Intentar con Groq ---
    print("[inference_net] 🌐 Intentando obtener productos desde Groq...")
    productos_groq = fetch_products_from_internet(uso, presupuesto, preferencias)

    if productos_groq:
        print(f"[inference_net] ✅ {len(productos_groq)} productos obtenidos desde Internet (Groq).")
        resultados = []

        # Insertar tarjeta de “Ajuste automático” si corresponde
        if ajustes_info:
            resultados.append({
                "product": {
                    "id": "ajuste-info",
                    "name": "Ajuste Automático del Sistema",
                    "brand": "SEAC",
                    "category": "Información",
                    "cpu": "",
                    "gpu": "",
                    "ram": "",
                    "storage": "",
                    "os": "",
                    "price": 0,
                    "url": ""
                },
                "score": 1.0,
                "reasons": [ajustes_info],
                "session_id": session_id
            })

        # Productos recomendados
        for p in productos_groq[:top_k]:
            producto = {
                "id": p.get("id", f"groq-{uuid.uuid4().hex[:6]}"),
                "name": p.get("modelo", "") or p.get("name", ""),
                "brand": p.get("marca", "") or p.get("brand", ""),
                "category": "laptop",
                "cpu": p.get("procesador", "") or p.get("cpu", ""),
                "gpu": p.get("tarjeta_grafica", "") or p.get("gpu", ""),
                "ram": p.get("memoria_ram", "") or p.get("ram", ""),
                "storage": p.get("almacenamiento", "") or p.get("storage", ""),
                "os": p.get("sistema_operativo", "") or p.get("os", ""),
                "price": float(p.get("precio", p.get("price", 0)) or 0),
                "url": p.get("link", "") or p.get("url", "")
            }

            # Explicación breve (si tu helper acepta 'uso' como 3er parámetro, déjalo; si no, quítalo)
            razones_brutas = [p.get("descripcion", "Recomendación generada desde Groq.")]
            try:
                explicacion = summarize_reasons_groq(producto["name"], razones_brutas, uso)
            except TypeError:
                # Compatibilidad si tu función tiene firma (name, reasons) sin 'uso'
                explicacion = summarize_reasons_groq(producto["name"], razones_brutas)

            resultados.append({
                "product": producto,
                "score": 1.0,
                "reasons": [explicacion],
                "session_id": session_id
            })
        return resultados

    # --- Fallback a catálogo local ---
    print("[inference_net] ⚠️ Groq no devolvió datos válidos. Usando catálogo local.")
    productos_locales = load_products()
    resultados = []

    if ajustes_info:
        resultados.append({
            "product": {
                "id": "ajuste-info",
                "name": "Ajuste Automático del Sistema",
                "brand": "SEAC",
                "category": "Información",
                "cpu": "",
                "gpu": "",
                "ram": "",
                "storage": "",
                "os": "",
                "price": 0,
                "url": ""
            },
            "score": 1.0,
            "reasons": [ajustes_info],
            "session_id": session_id
        })

    for prod in productos_locales[:top_k]:
        try:
            explicacion = summarize_reasons_groq(prod.get("name", "Producto"), ["Recomendación basada en catálogo local."], uso)
        except TypeError:
            explicacion = summarize_reasons_groq(prod.get("name", "Producto"), ["Recomendación basada en catálogo local."])

        resultados.append({
            "product": prod,
            "score": 1.0,
            "reasons": [explicacion],
            "session_id": session_id
        })

    return resultados[:top_k + (1 if ajustes_info else 0)]
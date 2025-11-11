import os, json, re, requests
from typing import List, Dict, Any, Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = (
    "Eres un experto en tecnología. Devuelve una lista JSON llamada 'laptops' o 'productos', "
    "con objetos que contengan: marca, modelo, cpu, gpu, ram, almacenamiento, sistema_operativo, "
    "precio (número), link y una descripcion natural que explique por qué este equipo es recomendable, "
    "para qué tipo de usuario o tarea es ideal, y sus ventajas principales."
)

def _call_groq_json(uso: str, presupuesto: float, preferencias: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if not GROQ_API_KEY:
        print("[api_internet] ⚠️ Falta GROQ_API_KEY en .env")
        return []

    prefs_text = json.dumps(preferencias or {}, ensure_ascii=False)
    user_prompt = (
        f"Necesito laptops para {uso}, con un presupuesto máximo de {presupuesto} USD. "
        f"Preferencias adicionales: {prefs_text}. Devuelve solo el JSON solicitado."
    )

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": GROQ_MODEL,
        "temperature": 0.4,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        r = requests.post(GROQ_ENDPOINT, headers=headers, json=body, timeout=60)
        r.raise_for_status()
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if "```" in content:
            content = re.sub(r"^```(json)?", "", content, flags=re.IGNORECASE).replace("```", "").strip()

        parsed = json.loads(content)
        if isinstance(parsed, dict):
            for k in ("laptops", "productos"):
                if k in parsed:
                    parsed = parsed[k]
                    break
        if isinstance(parsed, dict):
            parsed = [parsed]

        print(f"[api_internet] ✅ {len(parsed)} productos recibidos desde Groq.")
        return parsed

    except Exception as e:
        print(f"[api_internet] ❌ Error: {e}")
        return []

def _normalize_item(p: Dict[str, Any]) -> Dict[str, Any]:
    def g(k, *alts): 
        for key in (k,) + alts:
            if key in p and p[key] not in (None, ""):
                return str(p[key])
        return ""
    def num_price(v):
        try:
            return float(str(v).replace("$", "").replace(",", "").strip())
        except:
            return 0.0

    return {
        "marca": g("marca", "brand"),
        "modelo": g("modelo", "name"),
        "procesador": g("cpu"),
        "tarjeta_grafica": g("gpu"),
        "memoria_ram": g("ram"),
        "almacenamiento": g("almacenamiento", "storage"),
        "sistema_operativo": g("sistema_operativo", "os"),
        "precio": num_price(p.get("precio", p.get("price", 0))),
        "descripcion": g("descripcion", "description"),
        "link": g("link", "url"),
    }

def fetch_products_from_internet(uso: str, presupuesto: float, preferencias: Optional[Dict[str, Any]] = None, max_items: int = 8) -> List[Dict[str, Any]]:
    raw = _call_groq_json(uso, presupuesto, preferencias)
    if not raw:
        print("[api_internet] ⚠️ No se obtuvieron productos válidos de Groq.")
        return []
    out = [_normalize_item(x) for x in raw if isinstance(x, dict)]
    return out[:max_items]
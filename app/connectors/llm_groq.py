import os, requests

def summarize_reasons_groq(name: str, reasons: list[str], uso: str = "") -> str:
    """
    Genera una explicación más extensa (2-3 oraciones) en español natural sobre por qué este producto es recomendable.
    Usa Groq (Llama 3.3-70B) con un tono profesional y descriptivo.
    """

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return f"{name}: no se encontró GROQ_API_KEY en el entorno."

    # Nuevo prompt ampliado
    prompt = f"""
Eres un experto en tecnología que redacta reseñas profesionales y concisas.
Describe en 2 a 3 oraciones por qué este producto es recomendable para el usuario según su uso.

Producto: {name}
Uso previsto: {uso or 'general'}
Razones técnicas: {', '.join(reasons)}

Requisitos:
- Escribe en español fluido y natural, con tono profesional.
- Menciona los puntos más destacados (rendimiento, portabilidad, duración de batería, relación calidad-precio, etc.).
- Evita frases genéricas y redundantes.
- Máximo 80 palabras.
- No uses emojis ni listas.
Ejemplo de estilo:
"La ASUS ROG Zephyrus G14 ofrece gran potencia con su procesador Ryzen 9 y GPU RTX 4060. Ideal para jugadores y diseñadores que buscan equilibrio entre rendimiento y portabilidad, con un diseño elegante y compacto."
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 120,
            },
            timeout=25,
        )

        data = response.json()

        if "error" in data:
            return f"{name}: error de Groq API → {data['error'].get('message', str(data))}"

        if "choices" in data and data["choices"]:
            texto = data["choices"][0]["message"]["content"].strip()
            texto = texto.replace("\n", " ").replace('"', "").strip()
            return texto

        return f"{name}: respuesta inesperada de Groq."

    except requests.exceptions.Timeout:
        return f"{name}: tiempo de espera agotado con Groq."
    except Exception as e:
        return f"{name}: error general con Groq ({e})."
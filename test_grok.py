import requests, os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

print("Usando modelo:", model)

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
body = {
    "model": model,
    "messages": [
        {"role": "system", "content": "Eres un experto en laptops y tecnología."},
        {"role": "user", "content": "Dame 3 laptops gaming recientes en JSON con marca, modelo, cpu, gpu, ram, almacenamiento, sistema operativo, precio y link."}
    ],
    "temperature": 0.4,
    "response_format": {"type": "json_object"}
}

try:
    r = requests.post(url, headers=headers, json=body, timeout=60)
    print("Status:", r.status_code)
    print("Respuesta:", r.text[:500])
except Exception as e:
    print("❌ Error:", e)


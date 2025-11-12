# 💻 SE Onyx — Sistema Experto Asistente de Compras

Un sistema experto inteligente desarrollado con **FastAPI + SQL Server + JavaScript (Frontend)** que recomienda computadoras (laptops) de acuerdo con las **necesidades del usuario, su presupuesto, gama y preferencias de marca**.  
Combina **reglas de conocimiento**, **ajustes automáticos** y una integración híbrida con modelos LLM (Groq) para generar recomendaciones precisas y explicativas.

---

## 🚀 Características principales

✅ Recomendaciones automáticas de productos (por uso, gama y presupuesto)  
✅ Validación inteligente de rangos de presupuesto por gama (baja, media, alta)  
✅ Ajuste automático de parámetros insuficientes  
✅ Integración con **Groq API** para inferencia en línea (modo híbrido)  
✅ Sistema de favoritos por usuario (con validación antidual)  
✅ Sesiones persistentes con almacenamiento local  
✅ Base de datos SQL Server para sesiones, feedback, pesos y productos  
✅ Interfaz limpia, responsiva y moderna con **Bootstrap 5**

---

## 🧠 Arquitectura del proyecto

```
SEAC_proyecto_minimo_v0_1/
│
├── app/
│   ├── main.py                 # API principal de FastAPI
│   ├── inference_net.py        # Motor híbrido de inferencia (Groq + local)
│   ├── persistence_sql.py      # Persistencia en SQL Server
│   ├── learning.py             # Aprendizaje adaptativo (ajuste de pesos)
│   ├── db.py                   # Conexión a la base de datos (pyodbc)
│   ├── schemas.py              # Modelos Pydantic (Consulta, Producto, Feedback)
│   ├── api_internet.py         # Conector Groq (búsqueda de productos)
│   ├── connectors/
│   │   └── llm_groq.py         # Funciones de resumen e inferencia Groq
│   ├── templates/
│   │   ├── bienvenida.html     # Vista inicial (login, bienvenida)
│   │   └── index.html          # Interfaz principal del sistema experto
│   └── static/
│       ├── script.js           # Lógica frontend (consultas, favoritos, feedback)
│       ├── style.css           # Estilos personalizados
│       └── assets/             # Iconos, logos, imágenes
│
├── .env                        # Variables de entorno (DB, API_KEY)
├── requirements.txt            # Dependencias del proyecto
├── run_local.bat               # Ejecutar localmente (Windows)
├── run_ngrok.bat               # Ejecutar con túnel Ngrok
├── run.sh                      # Ejecución Linux/Mac
├── test_sql.py                 # Pruebas de conexión a SQL Server
├── test_grok.py                # Pruebas de conexión Groq API
└── README.md                   # Documentación del proyecto
```

---

## 🧩 Requisitos

### 🔧 Software necesario
- Python 3.10 o superior  
- Microsoft SQL Server 2019+  
- Node.js (opcional, para depuración de frontend)
- Ngrok (para exposición pública)

### 📦 Librerías Python
Instalar con:
```bash
pip install -r requirements.txt
```

#### Dependencias principales:
- fastapi  
- uvicorn  
- pyodbc  
- pydantic  
- python-dotenv  

---

## ⚙️ Configuración del entorno

### 🧾 Archivo `.env`
Modifica el archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
SQLSERVER_CONN=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=SEACDB;UID=sa;PWD=tu_contraseña
GROQ_API_KEY=tu_clave_de_groq
```

---

## 🗄️ Creación de la base de datos `SEACDB`

Ejecuta los siguientes comandos SQL en **SQL Server Management Studio**:

```sql
CREATE DATABASE SEACDB;
GO
```

---

## 🧭 Ejecución local

### 🔹 Windows
```bash
run_local.bat
```

### 🔹 Linux / Mac
```bash
bash run.sh
```

Luego abre en el navegador:  
👉 [http://localhost:8000/]

---

## 🌐 Exposición pública (Ngrok)

Si deseas compartir tu sistema públicamente:

```bash
ngrok http 8000
```

Obtendrás una URL como:
```
https://xxxxx.ngrok-free.app
```
Copia esa dirección y podrás acceder desde cualquier dispositivo.

---

## 🧠 Flujo de funcionamiento

1. El usuario ingresa al sistema (`/index`).
2. Selecciona **uso, gama y presupuesto**.
3. El sistema valida y ajusta automáticamente los valores incoherentes.
4. Se consulta a **Groq API** o al catálogo local (`inference_net.py`).
5. Los productos recomendados se muestran con su descripción detallada.
6. El usuario puede **guardar productos en favoritos**.
7. Se guarda feedback en base de datos y el sistema **aprende** de las selecciones.

---

## ⚡ Validaciones inteligentes

### Rango de presupuesto por gama:
| Gama | Mínimo | Máximo |
|------|---------|---------|
| Baja | $150 | $450 |
| Media | $451 | $900 |
| Alta | $901 | $2000 |

### Reglas automáticas:
- Si el presupuesto no coincide con la gama → alerta visual + ajuste automático.  
- Si el presupuesto es insuficiente para el uso (gaming, edición, etc.) → ajuste automático de gama y precio.  
- Se muestra mensaje informativo: “⚙️ Se ajustaron los parámetros para ofrecer opciones viables.”

---

## 🧩 Endpoints principales

| Endpoint | Método | Descripción |
|-----------|--------|--------------|
| `/infer` | POST | Genera recomendaciones según los parámetros del usuario |
| `/feedback` | POST | Registra feedback y agrega a favoritos si rating ≥ 0.8 |
| `/users/login` | POST | Inicio de sesión del usuario |
| `/users/register` | POST | Registro de nuevo usuario |
| `/users/{id}/favorites` | GET | Obtiene la lista de favoritos del usuario |
| `/health` | GET | Verifica el estado del servidor |

---

## 🧱 Estructura del frontend

El archivo principal del cliente es **`static/script.js`**, que maneja:

- Inicio y cierre de sesión  
- Envío de consultas al endpoint `/infer`  
- Validaciones de gama y presupuesto  
- Agregado a favoritos (`/feedback`)  
- Carga dinámica de tarjetas de productos  
- Alertas visuales y notificaciones con **Bootstrap Toasts**

El CSS personalizado se encuentra en **`static/style.css`** y adapta el diseño a cualquier dispositivo (responsive).

---

## 🧩 Licencia

Proyecto académico — libre de uso y modificación con fines educativos.  
© 2025 — *SE Onyx v1.0 — Sistema Experto Asistente de Compras*.

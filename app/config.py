# ==============================
# Configuración general del SEAC
# ==============================
# Carga de variables desde .env y metadatos de la app.

import os
from dotenv import load_dotenv
from .config import SEAC_SQLSERVER_CONN as SQLSERVER_CONN

load_dotenv()

# Clave para Groq (opcional). Si está vacía, el sistema usará el stub local.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Cadena de conexión a SQL Server (pyodbc)
SEAC_SQLSERVER_CONN = SQLSERVER_CONN

# Orígenes permitidos para CORS (separados por coma)
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")

# Metadatos
APP_NAME = "SEAC — Sistema Experto Asistente de Compras"
APP_VERSION = "1.0.0-ES"
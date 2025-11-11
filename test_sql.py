import pyodbc

conn_str = ("Tu cadena de conexión aquí"
)

try:
    conn = pyodbc.connect(conn_str, timeout=5)
    print("✅ Conexión exitosa a SQL Server!")
    conn.close()
except Exception as e:
    print("❌ Error de conexión:", e)

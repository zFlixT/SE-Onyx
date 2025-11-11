# =====================================================
# SEAC v1.3 — Base de datos SQL Server (autoinicialización)
# =====================================================
import os
import pyodbc

# Cadena de conexión: lee del entorno o usa un valor por defecto
SQLSERVER_CONN = os.getenv(
    "SEAC_SQLSERVER_CONN",
    "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=SEACDB;Trusted_Connection=yes;TrustServerCertificate=yes;"
)

# -----------------------------------------------------
# Función auxiliar para reemplazar base de datos en cadena
# -----------------------------------------------------
def _conn_replace_db(conn_str: str, new_db: str) -> str:
    parts = conn_str.split(";")
    out = []
    db_set = False
    for p in parts:
        if not p:
            continue
        kv = p.split("=", 1)
        if len(kv) == 2 and kv[0].strip().lower() in ("database", "initial catalog"):
            out.append(f"DATABASE={new_db}")
            db_set = True
        else:
            out.append(p)
    if not db_set:
        out.append(f"DATABASE={new_db}")
    return ";".join(out) + ";"

# -----------------------------------------------------
# Conexión segura (crea la BD si no existe)
# -----------------------------------------------------
def get_conn():
    try:
        return pyodbc.connect(SQLSERVER_CONN, autocommit=True)
    except pyodbc.Error:
        master_conn_str = _conn_replace_db(SQLSERVER_CONN, "master")
        mconn = pyodbc.connect(master_conn_str, autocommit=True)
        cur = mconn.cursor()
        dbname = "SEACDB"
        for frag in SQLSERVER_CONN.split(";"):
            if "=" in frag and frag.split("=")[0].strip().lower() in ("database", "initial catalog"):
                dbname = frag.split("=", 1)[1].strip()
        cur.execute(f"IF DB_ID('{dbname}') IS NULL CREATE DATABASE [{dbname}];")
        mconn.close()
        return pyodbc.connect(SQLSERVER_CONN, autocommit=True)

# -----------------------------------------------------
# Inicialización automática de las tablas del sistema
# -----------------------------------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # === Tabla de sesiones ===
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sessions]') AND type in (N'U'))
    CREATE TABLE [dbo].[sessions] (
        session_id NVARCHAR(100) NOT NULL PRIMARY KEY,
        uso NVARCHAR(255) NULL,
        presupuesto FLOAT NULL,
        created_at DATETIME NOT NULL DEFAULT(GETDATE())
    );
    """)

    # === Tabla de productos ===
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND type in (N'U'))
    CREATE TABLE [dbo].[products] (
        id NVARCHAR(100) NOT NULL PRIMARY KEY,
        name NVARCHAR(255) NULL,
        brand NVARCHAR(255) NULL,
        category NVARCHAR(100) NULL,
        cpu NVARCHAR(255) NULL,
        gpu NVARCHAR(255) NULL,
        ram NVARCHAR(50) NULL,
        storage NVARCHAR(50) NULL,
        os NVARCHAR(100) NULL,
        price FLOAT NULL,
        url NVARCHAR(MAX) NULL
    );
    """)

    # === Tabla de feedback ===
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[feedback]') AND type in (N'U'))
    CREATE TABLE [dbo].[feedback] (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        session_id NVARCHAR(100) NULL,
        product_id NVARCHAR(100) NULL,
        uso NVARCHAR(255) NULL,
        rating FLOAT NULL,
        ts DATETIME NOT NULL DEFAULT(GETDATE()),
        CONSTRAINT FK_feedback_sessions FOREIGN KEY (session_id) REFERENCES [dbo].[sessions](session_id)
    );
    """)

    # === Relación feedback → products ===
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_feedback_products')
    ALTER TABLE [dbo].[feedback]
    ADD CONSTRAINT FK_feedback_products FOREIGN KEY (product_id) REFERENCES [dbo].[products](id);
    """)

    # === Tabla de pesos ===
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[weights]') AND type in (N'U'))
    CREATE TABLE [dbo].[weights] (
        uso NVARCHAR(255) NOT NULL PRIMARY KEY,
        w_presupuesto FLOAT NULL,
        w_uso FLOAT NULL,
        w_marca FLOAT NULL
    );
    """)

        # Tabla de usuarios
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type in (N'U'))
    CREATE TABLE [dbo].[users] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        email NVARCHAR(255) UNIQUE NOT NULL,
        password NVARCHAR(255) NOT NULL,
        first_name NVARCHAR(120) NULL,
        last_name NVARCHAR(120) NULL,
        created_at DATETIME DEFAULT(GETDATE())
    );
    """)

    # Tabla de favoritos (relación usuario-producto)
    cur.execute("""
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[favorites]') AND type in (N'U'))
    CREATE TABLE [dbo].[favorites] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        product_id NVARCHAR(100) NOT NULL,
        added_at DATETIME DEFAULT(GETDATE()),
        CONSTRAINT FK_fav_user FOREIGN KEY (user_id) REFERENCES [dbo].[users](id),
        CONSTRAINT FK_fav_product FOREIGN KEY (product_id) REFERENCES [dbo].[products](id)
    );
    """)

    conn.close()
    print("✅ Tablas SEAC verificadas o creadas correctamente.")

# -----------------------------------------------------
# Crear base de datos si no existe al importar (una sola vez)
# -----------------------------------------------------
init_db()

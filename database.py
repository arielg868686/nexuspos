import os
import sqlite3
import psycopg2
import psycopg2.extras
from datetime import datetime

class Database:
    def __init__(self, db_file='nexuspos.db'):
        self.db_file = db_file
        self.is_postgres = os.environ.get('FLASK_ENV') == 'production'
        try:
            self.crear_tablas()
        except Exception as e:
            print(f"Error al crear tablas: {str(e)}")
            if self.is_postgres:
                print("Intentando usar SQLite como fallback...")
                self.is_postgres = False
                self.crear_tablas()

    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        if self.is_postgres:
            try:
                database_url = os.environ.get('DATABASE_URL')
                if not database_url:
                    raise ValueError("DATABASE_URL no está configurada")
                
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)
                
                conn = psycopg2.connect(database_url)
                conn.row_factory = psycopg2.extras.DictRow
                return conn
            except Exception as e:
                print(f"Error al conectar a PostgreSQL: {str(e)}")
                print("Cambiando a SQLite...")
                self.is_postgres = False
        
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def ejecutar(self, query, params=()):
        """Ejecuta una consulta SQL"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def obtener_uno(self, query, params=()):
        """Ejecuta una consulta y retorna un solo resultado"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()
        finally:
            conn.close()

    def obtener_todos(self, query, params=()):
        """Ejecuta una consulta y retorna todos los resultados"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        finally:
            conn.close()

    def crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        # Tabla de usuarios
        self.ejecutar('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT,
                rol TEXT NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de productos
        self.ejecutar('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                stock_minimo INTEGER NOT NULL DEFAULT 0,
                categoria TEXT NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de ventas
        self.ejecutar('''
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL,
                usuario_id INTEGER,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # Tabla de detalles de venta
        self.ejecutar('''
            CREATE TABLE IF NOT EXISTS detalles_venta (
                id SERIAL PRIMARY KEY,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')

        # Tabla de movimientos de stock
        self.ejecutar('''
            CREATE TABLE IF NOT EXISTS movimientos_stock (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                tipo_movimiento TEXT NOT NULL,
                motivo TEXT,
                usuario_id INTEGER,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # Insertar usuario demo si no existe
        self.ejecutar('''
            INSERT INTO usuarios (username, password, nombre, rol)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        ''', ('demo', 'demo123', 'Usuario Demo', 'admin'))

    def get_ventas_hoy(self):
        """Obtiene las ventas del día actual"""
        hoy = datetime.now().strftime('%Y-%m-%d')
        return self.obtener_todos('''
            SELECT v.*, u.nombre as usuario_nombre
            FROM ventas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE DATE(v.fecha) = ?
            ORDER BY v.fecha DESC
        ''', (hoy,))

    def get_productos_mas_vendidos(self, limite=5):
        """Obtiene los productos más vendidos"""
        return self.obtener_todos('''
            SELECT p.*, SUM(dv.cantidad) as total_vendido
            FROM detalles_venta dv
            JOIN productos p ON dv.producto_id = p.id
            GROUP BY p.id
            ORDER BY total_vendido DESC
            LIMIT ?
        ''', (limite,))

    def get_productos_bajo_stock(self):
        """Obtiene productos con stock por debajo del mínimo"""
        return self.obtener_todos('''
            SELECT * FROM productos 
            WHERE stock <= stock_minimo
            ORDER BY stock
        ''')

if __name__ == '__main__':
    db = Database() 
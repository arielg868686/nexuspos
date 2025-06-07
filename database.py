import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file='nexuspos.db'):
        self.db_file = db_file
        self.crear_tablas()

    def get_connection(self):
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def ejecutar(self, query, params=()):
        """Ejecuta una consulta SQL"""
        conn = self.get_connection()
        try:
            conn.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def obtener_uno(self, query, params=()):
        """Ejecuta una consulta y retorna un solo resultado"""
        conn = self.get_connection()
        try:
            return conn.execute(query, params).fetchone()
        finally:
            conn.close()

    def obtener_todos(self, query, params=()):
        """Ejecuta una consulta y retorna todos los resultados"""
        conn = self.get_connection()
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        # Tabla de usuarios
        self.ejecutar('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL,
                usuario_id INTEGER,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # Tabla de detalles de venta
        self.ejecutar('''
            CREATE TABLE IF NOT EXISTS detalles_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            INSERT OR IGNORE INTO usuarios (username, password, nombre, rol)
            VALUES (?, ?, ?, ?)
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
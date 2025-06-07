import os
import sqlite3
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_file = 'nexuspos.db'
        if os.environ.get('FLASK_ENV') == 'production':
            self.db_file = os.path.join(os.getcwd(), self.db_file)
        print(f"Usando base de datos en: {self.db_file}")
        
        try:
            # Intentar conectar a PostgreSQL primero
            database_url = os.environ.get('DATABASE_URL')
            if database_url and database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
                self.conn = sqlite3.connect(self.db_file)
                self.crear_tablas()
                return
        except Exception as e:
            print(f"Error al conectar a PostgreSQL: {str(e)}")
            print("Cambiando a SQLite...")
        
        # Si PostgreSQL falla o no está configurado, usar SQLite
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            self.crear_tablas()
        except Exception as e:
            print(f"Error al inicializar SQLite: {str(e)}")
            raise

    def crear_tablas(self):
        try:
            cursor = self.conn.cursor()
            
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT UNIQUE,
                    rol TEXT NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de productos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    precio REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    categoria TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de ventas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total REAL NOT NULL,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            ''')
            
            # Tabla de detalles de venta
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detalles_venta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER,
                    producto_id INTEGER,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas (id),
                    FOREIGN KEY (producto_id) REFERENCES productos (id)
                )
            ''')
            
            # Insertar usuario demo si no existe
            cursor.execute('''
                INSERT OR IGNORE INTO usuarios (username, password, rol)
                VALUES (?, ?, ?)
            ''', ('demo', 'demo123', 'admin'))
            
            self.conn.commit()
            logger.info("Tablas creadas correctamente")
        except Exception as e:
            logger.error(f"Error al crear tablas: {str(e)}")
            raise

    def obtener_uno(self, query, params=()):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error en obtener_uno: {str(e)}")
            raise

    def obtener_todos(self, query, params=()):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error en obtener_todos: {str(e)}")
            raise

    def ejecutar(self, query, params=()):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error en ejecutar: {str(e)}")
            self.conn.rollback()
            raise

    def get_connection(self):
        return self.conn

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
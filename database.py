import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_file = 'nexuspos.db'
        if os.environ.get('FLASK_ENV') == 'production':
            self.db_file = os.path.join(os.getcwd(), self.db_file)
        logger.info(f"Usando base de datos en: {self.db_file}")
        
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row
            self.crear_tablas()
        except Exception as e:
            logger.error(f"Error al inicializar SQLite: {str(e)}")
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
                    rol TEXT NOT NULL
                )
            ''')
            
            # Tabla de productos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    precio REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0
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
        try:
            hoy = datetime.now().strftime('%Y-%m-%d')
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as total_ventas, 
                       SUM(total) as total_ingresos
                FROM ventas 
                WHERE date(fecha) = ?
            ''', (hoy,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error al obtener ventas del día: {str(e)}")
            raise

    def get_productos_bajos_stock(self, limite=10):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM productos 
                WHERE stock <= ? 
                ORDER BY stock ASC
            ''', (limite,))
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error al obtener productos con bajo stock: {str(e)}")
            raise

    def get_productos_mas_vendidos(self, limite=5):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT p.*, SUM(dv.cantidad) as total_vendido
                FROM productos p
                JOIN detalles_venta dv ON p.id = dv.producto_id
                GROUP BY p.id
                ORDER BY total_vendido DESC
                LIMIT ?
            ''', (limite,))
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error al obtener productos más vendidos: {str(e)}")
            raise

if __name__ == '__main__':
    db = Database() 
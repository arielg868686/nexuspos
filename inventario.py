from datetime import datetime
import sqlite3

class GestorInventario:
    def __init__(self, db):
        self.db = db
        self.crear_tablas()

    def crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        self.db.ejecutar('''
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

        self.db.ejecutar('''
            CREATE TABLE IF NOT EXISTS movimientos_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                tipo_movimiento TEXT NOT NULL,
                motivo TEXT,
                usuario_id INTEGER,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')

    def obtener_producto(self, producto_id):
        """Obtiene un producto por su ID"""
        return self.db.obtener_uno('''
            SELECT * FROM productos WHERE id = ?
        ''', (producto_id,))

    def obtener_todos_productos(self, categoria='todos', orden='nombre'):
        """Obtiene todos los productos con filtros opcionales"""
        query = 'SELECT * FROM productos'
        params = []

        if categoria != 'todos':
            query += ' WHERE categoria = ?'
            params.append(categoria)

        if orden == 'nombre':
            query += ' ORDER BY nombre'
        elif orden == 'stock':
            query += ' ORDER BY stock'
        elif orden == 'precio':
            query += ' ORDER BY precio'

        return self.db.obtener_todos(query, tuple(params))

    def buscar_productos(self, query):
        """Busca productos por nombre o código"""
        return self.db.obtener_todos('''
            SELECT * FROM productos 
            WHERE nombre LIKE ? OR codigo LIKE ?
            ORDER BY nombre
        ''', (f'%{query}%', f'%{query}%'))

    def agregar_producto(self, datos):
        """Agrega un nuevo producto"""
        try:
            self.db.ejecutar('''
                INSERT INTO productos (codigo, nombre, descripcion, precio, stock, stock_minimo, categoria)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datos['codigo'],
                datos['nombre'],
                datos.get('descripcion', ''),
                datos['precio'],
                datos.get('stock', 0),
                datos.get('stock_minimo', 0),
                datos['categoria']
            ))
            return True
        except sqlite3.IntegrityError:
            return False

    def actualizar_producto(self, producto_id, datos):
        """Actualiza un producto existente"""
        try:
            self.db.ejecutar('''
                UPDATE productos 
                SET codigo = ?, nombre = ?, descripcion = ?, precio = ?, 
                    stock = ?, stock_minimo = ?, categoria = ?
                WHERE id = ?
            ''', (
                datos['codigo'],
                datos['nombre'],
                datos.get('descripcion', ''),
                datos['precio'],
                datos.get('stock', 0),
                datos.get('stock_minimo', 0),
                datos['categoria'],
                producto_id
            ))
            return True
        except sqlite3.IntegrityError:
            return False

    def eliminar_producto(self, producto_id):
        """Elimina un producto"""
        try:
            self.db.ejecutar('DELETE FROM productos WHERE id = ?', (producto_id,))
            return True
        except sqlite3.Error:
            return False

    def ajustar_stock(self, producto_id, cantidad, tipo_movimiento, motivo, usuario_id=None):
        """Ajusta el stock de un producto y registra el movimiento"""
        try:
            # Iniciar transacción
            self.db.ejecutar('BEGIN TRANSACTION')

            # Actualizar stock
            if tipo_movimiento == 'entrada':
                self.db.ejecutar('''
                    UPDATE productos 
                    SET stock = stock + ? 
                    WHERE id = ?
                ''', (cantidad, producto_id))
            else:  # salida
                self.db.ejecutar('''
                    UPDATE productos 
                    SET stock = stock - ? 
                    WHERE id = ?
                ''', (cantidad, producto_id))

            # Registrar movimiento
            self.db.ejecutar('''
                INSERT INTO movimientos_stock (producto_id, cantidad, tipo_movimiento, motivo, usuario_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (producto_id, cantidad, tipo_movimiento, motivo, usuario_id))

            # Confirmar transacción
            self.db.ejecutar('COMMIT')
            return True
        except sqlite3.Error:
            # Revertir cambios en caso de error
            self.db.ejecutar('ROLLBACK')
            return False

    def obtener_movimientos_stock(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene los movimientos de stock con filtros opcionales"""
        query = '''
            SELECT m.*, p.nombre as producto_nombre
            FROM movimientos_stock m
            JOIN productos p ON m.producto_id = p.id
        '''
        params = []

        if fecha_inicio and fecha_fin:
            query += ' WHERE m.fecha BETWEEN ? AND ?'
            params.extend([fecha_inicio, fecha_fin])

        query += ' ORDER BY m.fecha DESC'
        return self.db.obtener_todos(query, tuple(params))

    def obtener_categorias(self):
        """Obtiene todas las categorías únicas"""
        return self.db.obtener_todos('SELECT DISTINCT categoria FROM productos ORDER BY categoria')

    def obtener_productos_bajo_stock(self):
        """Obtiene productos con stock por debajo del mínimo"""
        return self.db.obtener_todos('''
            SELECT * FROM productos 
            WHERE stock <= stock_minimo
            ORDER BY stock
        ''')

    def obtener_estadisticas_inventario(self):
        """Obtiene estadísticas generales del inventario"""
        stats = {}
        
        # Total de productos
        stats['total_productos'] = self.db.obtener_uno('''
            SELECT COUNT(*) FROM productos
        ''')[0]

        # Valor total del inventario
        stats['valor_total'] = self.db.obtener_uno('''
            SELECT SUM(precio * stock) FROM productos
        ''')[0] or 0

        # Productos con stock bajo
        stats['productos_bajo_stock'] = self.db.obtener_uno('''
            SELECT COUNT(*) FROM productos WHERE stock <= stock_minimo
        ''')[0]

        # Productos sin stock
        stats['productos_sin_stock'] = self.db.obtener_uno('''
            SELECT COUNT(*) FROM productos WHERE stock = 0
        ''')[0]

        return stats 
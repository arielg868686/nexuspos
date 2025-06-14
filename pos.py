from database import Database
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PuntoDeVenta:
    def __init__(self, db):
        self.db = db
        self.carrito = []
        self.total = 0.0

    def agregar_producto(self, producto_id, cantidad):
        producto = self.db.obtener_uno('SELECT * FROM productos WHERE id = ?', (producto_id,))

        if not producto:
            return False, "Producto no encontrado"

        if producto['stock'] < cantidad:
            return False, "Stock insuficiente"

        # Verificar si el producto ya está en el carrito
        for item in self.carrito:
            if item['id'] == producto_id:
                if item['cantidad'] + cantidad > producto['stock']:
                    return False, "Stock insuficiente"
                item['cantidad'] += cantidad
                item['subtotal'] = item['cantidad'] * item['precio']
                self._calcular_total()
                return True, "Producto actualizado en el carrito"

        # Agregar nuevo producto al carrito
        self.carrito.append({
            'id': producto_id,
            'nombre': producto['nombre'],
            'precio': producto['precio'],
            'cantidad': cantidad,
            'subtotal': producto['precio'] * cantidad
        })
        self._calcular_total()
        return True, "Producto agregado al carrito"

    def quitar_producto(self, producto_id):
        self.carrito = [item for item in self.carrito if item['id'] != producto_id]
        self._calcular_total()
        return True, "Producto eliminado del carrito"

    def actualizar_cantidad(self, producto_id, nueva_cantidad):
        producto = self.db.obtener_uno('SELECT * FROM productos WHERE id = ?', (producto_id,))

        if not producto:
            return False, "Producto no encontrado"

        if producto['stock'] < nueva_cantidad:
            return False, "Stock insuficiente"

        for item in self.carrito:
            if item['id'] == producto_id:
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['cantidad'] * item['precio']
                self._calcular_total()
                return True, "Cantidad actualizada"

        return False, "Producto no encontrado en el carrito"

    def _calcular_total(self):
        self.total = sum(item['subtotal'] for item in self.carrito)

    def limpiar_carrito(self):
        self.carrito = []
        self.total = 0.0
        return True, "Carrito limpiado"

    def procesar_venta(self, usuario_id):
        if not self.carrito:
            return False, "El carrito está vacío"

        conn = self.db.get_connection()
        try:
            # Crear la venta
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ventas (fecha, total, usuario_id)
                VALUES (?, ?, ?)
            ''', (datetime.now(), self.total, usuario_id))
            venta_id = cursor.lastrowid

            # Agregar los detalles de la venta
            for item in self.carrito:
                cursor.execute('''
                    INSERT INTO detalles_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (venta_id, item['id'], item['cantidad'], item['precio'], item['subtotal']))

                # Actualizar el stock
                cursor.execute('''
                    UPDATE productos 
                    SET stock = stock - ? 
                    WHERE id = ?
                ''', (item['cantidad'], item['id']))

            conn.commit()
            self.limpiar_carrito()
            return True, f"Venta procesada exitosamente. ID: {venta_id}"

        except Exception as e:
            conn.rollback()
            return False, f"Error al procesar la venta: {str(e)}"
        finally:
            conn.close()

    def obtener_producto(self, codigo):
        return self.db.obtener_uno('''
            SELECT * FROM productos 
            WHERE codigo = ? OR nombre LIKE ?
        ''', (codigo, f'%{codigo}%'))

    def buscar_productos(self, termino):
        return self.db.obtener_todos('''
            SELECT * FROM productos 
            WHERE codigo LIKE ? OR nombre LIKE ?
            LIMIT 10
        ''', (f'%{termino}%', f'%{termino}%'))

    def get_ventas_hoy(self):
        try:
            hoy = datetime.now().strftime('%Y-%m-%d')
            cursor = self.db.get_connection().cursor()
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
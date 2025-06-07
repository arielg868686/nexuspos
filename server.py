from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from database import init_db, get_productos_bajo_stock, get_ventas_hoy, get_productos_mas_vendidos, Database
from pos import PuntoDeVenta
from inventario import GestorInventario
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'e8a521dd52efc86130c0c1392c5dc759')
app.config['SESSION_TYPE'] = 'filesystem'

# Configuración de la base de datos
if os.environ.get('FLASK_ENV') == 'production':
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///nexuspos.db')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexuspos.db'

# Inicializar la base de datos
db = Database()
db.crear_tablas()  # Asegurarse de que las tablas existan

# Inicializar el punto de venta
pos = PuntoDeVenta(db)

# Inicializar el gestor de inventario
inventario = GestorInventario(db)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/demo')
def demo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('demo.html')

@app.route('/pos')
def pos_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('pos.html')

@app.route('/inventario')
def inventario_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats = inventario.obtener_estadisticas_inventario()
    categorias = inventario.obtener_categorias()
    productos = inventario.obtener_todos_productos()
    movimientos = inventario.obtener_movimientos_stock()
    
    return render_template('inventario.html', 
                         stats=stats,
                         categorias=categorias,
                         productos=productos,
                         movimientos=movimientos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'demo' and password == 'demo123':
            session['user_id'] = 1
            return redirect(url_for('demo'))
        
        return render_template('login.html', error='Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/productos')
def api_productos():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    categoria = request.args.get('categoria', 'todos')
    conn = get_db_connection()
    
    if categoria == 'todos':
        productos = conn.execute('SELECT * FROM productos ORDER BY nombre').fetchall()
    else:
        productos = conn.execute('SELECT * FROM productos WHERE categoria = ? ORDER BY nombre', (categoria,)).fetchall()
    
    conn.close()
    return jsonify([dict(p) for p in productos])

@app.route('/api/productos/buscar')
def api_buscar_productos():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    termino = request.args.get('q', '')
    productos = pos.buscar_productos(termino)
    return jsonify([dict(p) for p in productos])

@app.route('/api/carrito')
def api_carrito():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    return jsonify({
        'items': pos.carrito,
        'total': pos.total
    })

@app.route('/api/carrito/agregar', methods=['POST'])
def api_agregar_al_carrito():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    success, message = pos.agregar_producto(data['producto_id'], data['cantidad'])
    return jsonify({'success': success, 'message': message})

@app.route('/api/carrito/actualizar', methods=['POST'])
def api_actualizar_carrito():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    success, message = pos.actualizar_cantidad(data['producto_id'], data['cantidad'])
    return jsonify({'success': success, 'message': message})

@app.route('/api/carrito/quitar', methods=['POST'])
def api_quitar_del_carrito():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    success, message = pos.quitar_producto(data['producto_id'])
    return jsonify({'success': success, 'message': message})

@app.route('/api/ventas/procesar', methods=['POST'])
def api_procesar_venta():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    success, message = pos.procesar_venta(session.get('user_id', 1))
    return jsonify({'success': success, 'message': message})

@app.route('/api/productos/bajo-stock')
def api_productos_bajo_stock():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    productos = get_productos_bajo_stock()
    return jsonify([dict(p) for p in productos])

@app.route('/api/ventas/hoy')
def api_ventas_hoy():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    ventas = get_ventas_hoy()
    return jsonify(dict(ventas))

@app.route('/api/productos/mas-vendidos')
def api_productos_mas_vendidos():
    if 'authenticated' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    productos = get_productos_mas_vendidos()
    return jsonify([dict(p) for p in productos])

@app.route('/salud')
def salud():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
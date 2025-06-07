from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys
import logging
from database import Database
from pos import PuntoDeVenta
from inventario import GestorInventario
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar el entorno
if os.environ.get('RENDER'):
    os.environ['FLASK_ENV'] = 'production'
    logger.info("Configurando entorno de producción...")
    logger.info(f"Directorio actual: {os.getcwd()}")
    logger.info(f"Contenido del directorio: {os.listdir('.')}")
else:
    os.environ['FLASK_ENV'] = 'development'
    logger.info("Configurando entorno de desarrollo...")

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_123')
app.config['SESSION_TYPE'] = 'filesystem'

# Configurar la base de datos
try:
    db = Database()
    logger.info("Base de datos inicializada correctamente")
except Exception as e:
    logger.error(f"Error al inicializar la base de datos: {str(e)}")
    raise

# Inicializar componentes
try:
    pos = PuntoDeVenta(db)
    inventario = GestorInventario(db)
    logger.info("Componentes POS e Inventario inicializados correctamente")
except Exception as e:
    logger.error(f"Error al inicializar componentes: {str(e)}")
    raise

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Usuario(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    try:
        user = db.obtener_uno("SELECT * FROM usuarios WHERE id = ?", (user_id,))
        if user:
            return Usuario(user['id'], user['username'])
        return None
    except Exception as e:
        logger.error(f"Error al cargar usuario: {str(e)}")
        return None

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error al renderizar index: {str(e)}")
        return "Error interno del servidor", 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        logger.error(f"Error al servir archivo estático {filename}: {str(e)}")
        return "Archivo no encontrado", 404

@app.route('/demo')
@login_required
def demo():
    return render_template('demo.html')

@app.route('/pos')
@login_required
def pos_page():
    return render_template('pos.html')

@app.route('/inventario')
@login_required
def inventario_page():
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
            user = Usuario(1, 'demo')
            login_user(user)
            session['authenticated'] = True
            return redirect(url_for('demo'))
        
        return render_template('login.html', error='Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/productos')
@login_required
def api_productos():
    categoria = request.args.get('categoria', 'todos')
    productos = inventario.obtener_todos_productos(categoria=categoria)
    return jsonify([dict(p) for p in productos])

@app.route('/api/productos/buscar')
@login_required
def api_buscar_productos():
    termino = request.args.get('q', '')
    productos = pos.buscar_productos(termino)
    return jsonify([dict(p) for p in productos])

@app.route('/api/carrito')
@login_required
def api_carrito():
    return jsonify({
        'items': pos.carrito,
        'total': pos.total
    })

@app.route('/api/carrito/agregar', methods=['POST'])
@login_required
def api_agregar_al_carrito():
    data = request.get_json()
    success, message = pos.agregar_producto(data['producto_id'], data['cantidad'])
    return jsonify({'success': success, 'message': message})

@app.route('/api/carrito/actualizar', methods=['POST'])
@login_required
def api_actualizar_carrito():
    data = request.get_json()
    success, message = pos.actualizar_cantidad(data['producto_id'], data['cantidad'])
    return jsonify({'success': success, 'message': message})

@app.route('/api/carrito/quitar', methods=['POST'])
@login_required
def api_quitar_del_carrito():
    data = request.get_json()
    success, message = pos.quitar_producto(data['producto_id'])
    return jsonify({'success': success, 'message': message})

@app.route('/api/ventas/procesar', methods=['POST'])
@login_required
def api_procesar_venta():
    success, message = pos.procesar_venta(current_user.id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/productos/bajo-stock')
@login_required
def api_productos_bajo_stock():
    productos = inventario.obtener_productos_bajo_stock()
    return jsonify([dict(p) for p in productos])

@app.route('/api/ventas/hoy')
@login_required
def api_ventas_hoy():
    ventas = db.get_ventas_hoy()
    return jsonify([dict(v) for v in ventas])

@app.route('/api/productos/mas-vendidos')
@login_required
def api_productos_mas_vendidos():
    productos = db.get_productos_mas_vendidos()
    return jsonify([dict(p) for p in productos])

@app.route('/salud')
def salud():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    try:
        logger.info("Iniciando aplicación...")
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {str(e)}")
        raise 
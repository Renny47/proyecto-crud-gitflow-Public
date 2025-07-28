import os
import urllib
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configuración de Flask
app = Flask(__name__)
app.secret_key = 'clave_super_secreta'

# Configuración de conexión a SQL Server con autenticación de Windows
params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=ARSH-JFKTEC120\\SQLEXPRESS;"
    "DATABASE=SistemaGestion;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar base de datos
db = SQLAlchemy(app)

# Modelos
class Usuario(db.Model):
    __tablename__ = 'Usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), default='usuario')  # admin, usuario
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Cliente(db.Model):
    __tablename__ = 'Clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), nullable=False, unique=True)
    telefono = db.Column(db.String(20))

class Categoria(db.Model):
    __tablename__ = 'Categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)

class Proveedor(db.Model):
    __tablename__ = 'Proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    contacto = db.Column(db.String(100), nullable=False)

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir rol de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        
        user = Usuario.query.get(session['user_id'])
        if not user or user.rol != 'admin':
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Usuario.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.activo:
            session['user_id'] = user.id
            session['username'] = user.username
            session['nombre_completo'] = user.nombre_completo
            session['rol'] = user.rol
            flash(f'Bienvenido, {user.nombre_completo}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        nombre_completo = request.form['nombre_completo']
        
        # Validaciones
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return render_template('registro.html')
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return render_template('registro.html')
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            username=username,
            email=email,
            nombre_completo=nombre_completo,
            rol='usuario'
        )
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash('Usuario registrado exitosamente. Puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('registro.html')

# Rutas CRUD (protegidas con login_required)

@app.route('/')
@login_required
def index():
    stats = {
        'clientes': Cliente.query.count(),
        'categorias': Categoria.query.count(),
        'proveedores': Proveedor.query.count()
    }
    return render_template('index.html', stats=stats)

# ------------------- CLIENTES -------------------
@app.route('/clientes')
@login_required
def clientes():
    return render_template('clientes.html', clientes=Cliente.query.all())

@app.route('/clientes/crear', methods=['POST'])
@login_required
def crear_cliente():
    nombre = request.form['nombre']
    correo = request.form['correo']
    telefono = request.form['telefono']
    if Cliente.query.filter_by(correo=correo).first():
        flash("Correo ya existe", "error")
        return redirect(url_for('clientes'))
    nuevo = Cliente(nombre=nombre, correo=correo, telefono=telefono)
    db.session.add(nuevo)
    db.session.commit()
    flash("Cliente creado exitosamente", "success")
    return redirect(url_for('clientes'))

@app.route('/clientes/editar/<int:id>', methods=['POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    cliente.nombre = request.form['nombre']
    cliente.correo = request.form['correo']
    cliente.telefono = request.form['telefono']
    db.session.commit()
    flash("Cliente actualizado", "success")
    return redirect(url_for('clientes'))

@app.route('/clientes/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminado", "success")
    return redirect(url_for('clientes'))

# ------------------- CATEGORIAS -------------------
@app.route('/categorias')
@login_required
def categorias():
    return render_template('categorias.html', categorias=Categoria.query.all())

@app.route('/categorias/crear', methods=['POST'])
@login_required
def crear_categoria():
    nombre = request.form['nombre']
    if Categoria.query.filter_by(nombre=nombre).first():
        flash("Categoría ya existe", "error")
        return redirect(url_for('categorias'))
    nueva = Categoria(nombre=nombre)
    db.session.add(nueva)
    db.session.commit()
    flash("Categoría creada", "success")
    return redirect(url_for('categorias'))

@app.route('/categorias/editar/<int:id>', methods=['POST'])
@login_required
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    categoria.nombre = request.form['nombre']
    db.session.commit()
    flash("Categoría actualizada", "success")
    return redirect(url_for('categorias'))

@app.route('/categorias/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    flash("Categoría eliminada", "success")
    return redirect(url_for('categorias'))

# ------------------- PROVEEDORES -------------------
@app.route('/proveedores')
@login_required
def proveedores():
    return render_template('proveedores.html', proveedores=Proveedor.query.all())

@app.route('/proveedores/crear', methods=['POST'])
@login_required
def crear_proveedor():
    nombre = request.form['nombre']
    contacto = request.form['contacto']
    if Proveedor.query.filter_by(nombre=nombre).first():
        flash("Proveedor ya existe", "error")
        return redirect(url_for('proveedores'))
    nuevo = Proveedor(nombre=nombre, contacto=contacto)
    db.session.add(nuevo)
    db.session.commit()
    flash("Proveedor creado", "success")
    return redirect(url_for('proveedores'))

@app.route('/proveedores/editar/<int:id>', methods=['POST'])
@login_required
def editar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    proveedor.nombre = request.form['nombre']
    proveedor.contacto = request.form['contacto']
    db.session.commit()
    flash("Proveedor actualizado", "success")
    return redirect(url_for('proveedores'))

@app.route('/proveedores/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_proveedor(id):
    proveedor = Proveedor.query.get_or_404(id)
    db.session.delete(proveedor)
    db.session.commit()
    flash("Proveedor eliminado", "success")
    return redirect(url_for('proveedores'))

# Crear tablas si no existen y verificar conexión
with app.app_context():
    try:
        db.session.execute('SELECT 1')
        print("✅ Conexión exitosa a SQL Server")
        db.create_all()
        
        # Crear usuario administrador por defecto si no existe
        admin_user = Usuario.query.filter_by(username='admin').first()
        if not admin_user:
            admin = Usuario(
                username='admin',
                email='admin@sistema.com',
                nombre_completo='Administrador del Sistema',
                rol='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario administrador creado - Usuario: admin, Contraseña: admin123")
        
    except Exception as e:
        print("❌ Error de conexión a SQL Server:", str(e))


# ------------------- RUN -------------------
if __name__ == '__main__':
    app.run(debug=True)

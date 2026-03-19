from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from pymysql.cursors import DictCursor
from functools import wraps
from dotenv import load_dotenv
import os
import re
import cloudinary
import cloudinary.uploader
import pymysql

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "cambiame_por_un_valor_seguro")
app.permanent_session_lifetime = 60 * 60 * 24 * 7  # 7 días (opcional)

# Config Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)




# Función para conectar a MySQL con PyMySQL
def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def validar_email(email: str) -> bool:
    # validación simple
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None

def login_required(f):
    # decorator simple para proteger rutas
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Debes iniciar sesión para ver esa página.", "warning")
            return redirect(url_for("loguear"))
        return f(*args, **kwargs)
    return decorated


@app.before_request
def load_user():
    g.user = session.get("user")


@app.context_processor
def inject_user():
    return {"user": session.get("user")}

# Ruta principal (registro)
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("psw", "")

        # Validaciones mínimas
        if not nombre or not email or not password:
            flash("Nombre, email y contraseña son obligatorios.", "danger")
            return redirect(url_for("register"))
        if not validar_email(email):
            flash("Email no válido.", "danger")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)  # por defecto pbkdf2:sha256

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                sql = """INSERT INTO usuario_admin (nombre, apellido, telefono, email, psw)
                         VALUES (%s, %s, %s, %s, %s)"""
                cur.execute(sql, (nombre, apellido, telefono, email, hashed))

                conn.commit()
            flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("loguear"))
        except pymysql.err.IntegrityError:
            flash("El email ya está en uso.", "danger")
            return redirect(url_for("register"))
        finally:
            conn.close()

    return render_template("register.html")

# Login
@app.route("/login", methods=["GET","POST"])
def loguear():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email y contraseña requeridos.", "danger")
            return redirect(url_for("loguear"))

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM usuario_admin WHERE email = %s", (email,))
                user = cur.fetchone()
            if user and check_password_hash(user["psw"], password):
                # guardar lo mínimo en sesión
                session.permanent = True  # si quieres sesión persistente
                session["user"] = {
                    "id": user["id_usuario"],
                    "nombre": user["nombre"],
                    "email": user["email"]
                }
                flash(f"Bienvenido, {user['nombre']}!", "success")
                return redirect(url_for("index"))
            else:
                flash("Credenciales incorrectas.", "danger")
                return redirect(url_for("loguear"))
        finally:
            conn.close()

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("index"))



@app.route("/administradores")
@login_required
def administradores():
    # Asegurarse de que el user esté en session
    user = session.get("user")
    if not user:
        flash("Debes iniciar sesión.", "warning")
        return redirect(url_for("loguear"))

    id_usuario = user.get("id")
    administrador = None
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Seleccionamos SOLO las columnas que queremos mostrar (sin psw)
            cursor.execute(
                "SELECT id_usuario, Nombre, Apellido, Telefono, Email, fecha_registro "
                "FROM usuario_admin WHERE id_usuario = %s",
                (id_usuario,)
            )
            administrador = cursor.fetchone()  # un solo registro
    except pymysql.MySQLError:
        app.logger.exception("Error al traer administrador")
        flash("Error al cargar datos.", "danger")
    finally:
        if conn:
            conn.close()

    # administradores es un dict o None
    return render_template("administradores.html", administrador=administrador)


@app.route("/editara/<int:id>", methods=["GET", "POST"])
@login_required
def editar_admin(id):


    conn = get_connection()
    if request.method == "POST":
        nombre = request.form.get("Nombre","").strip()
        apellido = request.form.get("Apellido","").strip()
        telefono = request.form.get("Telefono","").strip()
        email = request.form.get("Email","").strip().lower()
        password = request.form.get("Password","")
        
        errores = []
        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not email:
            errores.append("El email es obligatorio.")
        elif not validar_email(email):
            errores.append("Email no válido.")
        if password and len(password) < 6:
            errores.append("Si cambias la contraseña, debe tener al menos 6 caracteres.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return redirect(url_for("editar_admin", id=id))

        hashed = generate_password_hash(password) if password else None


        if conn:
            try:
                conn = get_connection()
                with conn.cursor() as cursor:
                    if hashed:
                        query = """
                            UPDATE usuario_admin
                            SET Nombre=%s, Apellido=%s, Telefono=%s, Email=%s, psw=%s
                            WHERE id_usuario=%s
                        """
                        params = (nombre, apellido, telefono, email, hashed, id)
                    else:
                        # No actualizar la contraseña
                        query = """
                            UPDATE usuario_admin
                            SET Nombre=%s, Apellido=%s, Telefono=%s, Email=%s
                            WHERE id_usuario=%s
                        """
                        params = (nombre, apellido, telefono, email, id)

                    cursor.execute(query, params)
                    conn.commit()

                flash("Datos actualizados correctamente.", "success")
                return redirect(url_for("administradores"))
            except pymysql.MySQLError as err:
                app.logger.exception("Error al actualizar usuario")
                flash("Ocurrió un error al actualizar el usuario.", "danger")
                return redirect(url_for("administradores"))
            finally:
                if conn:
                    conn.close()


    # si es GET → mostrar datos actuales
    conn = None
    admin = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuario_admin WHERE id_usuario=%s", (id,))
            admin = cursor.fetchone()
    except pymysql.MySQLError:
        app.logger.exception("Error al leer usuario")
        flash("No se pudo cargar la información del usuario.", "danger")
        return redirect(url_for("administradores"))
    finally:
        if conn:
            conn.close()

    if not admin:
        flash("Usuario no encontrado.", "warning")
        return redirect(url_for("administradores"))

    # Renderiza la plantilla con el admin (un dict)
    return render_template("editara.html", admin=admin)


@app.route("/editarp/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):


    conn = get_connection()
    if request.method == "POST":
        descripcion = request.form.get("descripcion")
        precio = request.form.get("precio")
        contenido = request.form.get("contenido")
        stock = request.form.get("stock")
        file = request.files.get("imagen")
        categoria = request.form.get("categoria")

        imagen_url = None
        if file and file.filename != "":
            # Subir imagen nueva a Cloudinary
            resultado = cloudinary.uploader.upload(file)
            imagen_url = resultado.get("secure_url")

        if conn:
            try:
                with conn.cursor() as cursor:
                    if imagen_url:
                        # Si hay nueva imagen
                        query = """
                            UPDATE productos
                            SET descripcion=%s, precio=%s, stock=%s, imagen=%s, id_categoria=%s
                            WHERE id_producto=%s
                        """
                        cursor.execute(query, (descripcion, precio, stock, imagen_url, categoria, id))
                        conn.commit()
                        print(categoria)

                        return redirect("/productos")
                    else:
                        # Si no se subió imagen, no actualizar ese campo
                        query = """
                            UPDATE productos
                            SET descripcion=%s, precio=%s, contenido=%s, stock=%s, id_categoria=%s
                            WHERE id_producto=%s
                        """
                        cursor.execute(query, (descripcion, precio, contenido, stock, categoria, id))
                        conn.commit()

                        return redirect("/productos")
            except pymysql.MySQLError as err:
                print(f"❌ Error al actualizar: {err}")
            finally:
                conn.close()

        return redirect("/productos")

    # si es GET → mostrar datos actuales
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM productos WHERE id_producto=%s", (id,))
                producto = cursor.fetchone()
        except pymysql.MySQLError as err:
            print(f"❌ Error en MySQL: {err}")
        finally:
            conn.close()
        

    return render_template("editarp.html", producto=producto)


@app.route("/eliminarp/<int:id>", methods=["POST"])
@login_required
def eliminar_producto(id):

    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("catalogo"))  # Cambia la ruta según la tuya


@app.route("/productos")
def catalogo():
    conn = get_connection()
    productos = []
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM productos")
                productos = cursor.fetchall()
        except pymysql.MySQLError as err:
            print(f"Error en MySQL: {err}")
        finally:
            conn.close()
    return render_template("productos.html", productos=productos)


@app.route("/subir", methods=["GET", "POST"])
@login_required
def subir():
        if request.method == "POST":
            user = session.get("user")
            nombre = request.form.get("nombre")
            marca = request.form.get("marca")
            descripcion = request.form.get("descripcion")
            precio = request.form.get("precio")
            contenido = request.form.get("contenido")
            stock = request.form.get("stock")
            file = request.files.get("imagen")
            id_categoria = request.form.get("categoria")
            id_usuario = user.get("id")


            try:
                # Subir imagen a Cloudinary
                resultado = cloudinary.uploader.upload(file)
                imagen_url = resultado.get("secure_url")

                # Guardar en la base de datos
                conn = get_connection()
                with conn.cursor() as cursor:
                    query = """
                        INSERT INTO productos 
                        (nombre, marca, descripcion, precio, contenido, stock, imagen, id_categoria, id_usuario) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, (nombre, marca, descripcion, precio, contenido, stock, imagen_url, id_categoria, id_usuario))
                    conn.commit()
                    print(nombre, marca, descripcion, precio, contenido, stock, imagen_url, id_categoria, id_usuario)

                conn.close()
                flash("✅ Producto subido correctamente")
                return redirect(url_for("catalogo"))

            except Exception as e:
                app.logger.exception("Error subiendo producto!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                flash(f"❌ Error: {e}")
                return redirect(request.url)

        return render_template("subir.html")



@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor()
    # 1️⃣ Novedades: los últimos agregados
    cursor.execute("SELECT * FROM productos ORDER BY id_producto DESC LIMIT 8")
    novedades = cursor.fetchall()
    
    # 2️⃣ Más vendidos (usamos stock por ahora)
    cursor.execute("SELECT * FROM productos ORDER BY stock DESC LIMIT 8")
    mas_vendidos = cursor.fetchall()

    # 3️⃣ Shampo (Traemos el todos losproductos que tengan la categoria shampoo)

    cursor.execute("SELECT * FROM productos WHERE id_categoria = 1 LIMIT 8")

    shampoo = cursor.fetchall()

    conn.close()

    # 🔙 Enviamos todo a index.html
    return render_template(
        "index.html",
        novedades=novedades,
        mas_vendidos=mas_vendidos,
        shampoo=shampoo,
    )


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        like = f"%{q}%"
        conn = get_connection()
        try:
            with conn.cursor() as cur:                  
                cur.execute("SELECT * FROM productos WHERE nombre LIKE %s", (like,))
                results = cur.fetchall()
        except pymysql.MySQLError as err:
            app.logger.exception("Error en búsqueda")
            results = []
        finally:
            conn.close()
    return render_template('search_results.html', q=q, resultados=results)


@app.route('/productos/<int:id>')
def renderizar_cat(id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM productos WHERE id_categoria = %s", (id,))
            results = cur.fetchall()
    except pymysql.MySQLError as err:
        app.logger.exception("Error en Busqueda")
        results = []
    finally:
        conn.close()   

    return render_template('productos.html', productos=results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3030, debug=True)

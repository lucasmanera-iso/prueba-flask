from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import pymysql

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "devkey")

# Config Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


usuarios = []

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


# Ruta principal (registro)
@app.route("/register", methods=["GET", "POST"])
def register():
    mensaje = ""
    if usuarios:
        if request.method == "POST":
            nombre = request.form.get("Nombre")
            apellido = request.form.get("Apellido")
            telefono = request.form.get("Telefono")
            email = request.form.get("Email")
            psw = request.form.get("psw")

            conn = get_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        query = "INSERT INTO usuario_admin (Nombre, Apellido, Telefono, Email, Psw) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(query, (nombre, apellido,telefono, email, psw))
                        conn.commit()
                    mensaje = "✅ Usuario registrado correctamente!"
                    return redirect("/")
                except pymysql.MySQLError as err:
                    mensaje = f"❌ Error al insertar en MySQL: {err}"
                finally:
                    conn.close()
            else:
                mensaje = "❌ Error de conexión con la base de datos."
    else:
        return redirect("/")

    return render_template("register.html", mensaje=mensaje)


# Login
@app.route("/login", methods=["GET", "POST"])
def logear():
    mensaje = ""
    if request.method == "POST":
        Email = request.form.get("Email")
        password = request.form.get("password")

        conn = get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    query = "SELECT * FROM usuario_admin WHERE Email=%s AND Psw=%s"
                    cursor.execute(query, (Email, password))
                    user = cursor.fetchone()
                if user:
                    usuarios.append(user)
                    return redirect("/administradores")
                else:
                    mensaje = "❌ Usuario o contraseña incorrectos."
            except pymysql.MySQLError as err:
                mensaje = f"❌ Error en MySQL: {err}"
            finally:
                conn.close()
        else:
            mensaje = "❌ Error de conexión con la base de datos."

    return render_template("login.html", mensaje=mensaje)


@app.route("/administradores")
def administradores():
    if not usuarios:  # si no hay nadie logueado, redirige
        return redirect(url_for("logear"))

    conn = get_connection()
    administradores = []
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM usuario_admin")
                administradores = cursor.fetchall()
        except pymysql.MySQLError as err:
            print(f"❌ Error en MySQL: {err}")
        finally:
            conn.close()

    return render_template("administradores.html", administradores=administradores)


@app.route("/editara/<int:id>", methods=["GET", "POST"])
def editar_admin(id):
    if not usuarios:
        return redirect(url_for("logear"))

    conn = get_connection()
    if request.method == "POST":
        nombre = request.form.get("Nombre")
        apellido = request.form.get("Apellido")
        telefono = request.form.get("Telefono")
        email = request.form.get("Email")

        if conn:
            try:
                with conn.cursor() as cursor:
                    query = """
                        UPDATE usuario_admin
                        SET Nombre=%s, Apellido=%s, Telefono=%s, Email=%s
                        WHERE id_usuario=%s
                    """
                    cursor.execute(query, (nombre, apellido, telefono, email, id))
                    conn.commit()
            except pymysql.MySQLError as err:
                print(f"❌ Error al actualizar: {err}")
            finally:
                conn.close()

        return redirect(url_for("administradores"))

    # si es GET → mostrar datos actuales
    admin = None
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM usuario_admin WHERE id_usuario=%s", (id,))
                admin = cursor.fetchone()
        except pymysql.MySQLError as err:
            print(f"❌ Error en MySQL: {err}")
        finally:
            conn.close()
        
        usuario = next((u for u in usuarios if u["id_usuario"] == id), None)

    return render_template("editara.html", usuario=usuario)


@app.route("/editarp/<int:id>", methods=["GET", "POST"])
def editar_producto(id):
    if not usuarios:
        return redirect(url_for("logear"))

    conn = get_connection()
    if request.method == "POST":
        descripcion = request.form.get("descripcion")
        precio = request.form.get("precio")
        contenido = request.form.get("contenido")
        stock = request.form.get("stock")
        file = request.files.get("imagen")

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
                            SET descripcion=%s, precio=%s, stock=%s, imagen=%s
                            WHERE id_producto=%s
                        """
                        cursor.execute(query, (descripcion, precio, stock, imagen_url, id))
                        conn.commit()

                        return redirect("/productos")
                    else:
                        # Si no se subió imagen, no actualizar ese campo
                        query = """
                            UPDATE productos
                            SET descripcion=%s, precio=%s, contenido=%s, stock=%s
                            WHERE id_producto=%s
                        """
                        cursor.execute(query, (descripcion, precio, contenido, stock, id))
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
    return render_template("productos.html", productos=productos, usuarios=usuarios)


@app.route("/subir", methods=["GET", "POST"])
def subir():
    if usuarios:  # validación de login
        if request.method == "POST":
            nombre = request.form.get("nombre")
            marca = request.form.get("marca")
            descripcion = request.form.get("descripcion")
            precio = request.form.get("precio")
            contenido = request.form.get("contenido")
            stock = request.form.get("stock")
            file = request.files.get("imagen")
            id_categoria = request.form.get("categoria")
            id_usuario = usuarios[0]["id_usuario"]


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
                app.logger.exception("Error subiendo producto")
                flash(f"❌ Error: {e}")
                return redirect(request.url)

        return render_template("subir.html")

    return redirect(url_for("logear"))


# Home (si está logueado)
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
<<<<<<< HEAD
    cursor.execute("SELECT * FROM productos WHERE id_categoria = 4 LIMIT 8")
=======
    cursor.execute("SELECT * FROM productos WHERE id_categoria = 2 LIMIT 8")
>>>>>>> 21b424899dc153010ad2af328ceedd6f26563c1a
    shampoo = cursor.fetchall()

    conn.close()

    # 🔙 Enviamos todo a index.html
    return render_template(
        "index.html",
        novedades=novedades,
        mas_vendidos=mas_vendidos,
        shampoo=shampoo,
        usuarios=usuarios
    )




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3030, debug=True)

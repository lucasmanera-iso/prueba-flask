from flask import Flask, render_template, request, url_for, redirect
import pymysql

app = Flask(__name__)

usuarios = []

# Función para conectar a MySQL con PyMySQL
def get_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="1233",
            database="catalogo",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Conectado correctamente a MySQL con PyMySQL")
        return connection
    except pymysql.MySQLError as err:
        print(f"❌ Error al conectar con MySQL: {err}")
        return None


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
                    return redirect(url_for("/"))
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
                    usuarios.append(Email)
                    return redirect(url_for("logueado"))
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


@app.route("/editar/<int:id>", methods=["GET", "POST"])
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
                cursor.execute("SELECT * FROM usuario_admin WHERE id=%s", (id,))
                admin = cursor.fetchone()
        except pymysql.MySQLError as err:
            print(f"❌ Error en MySQL: {err}")
        finally:
            conn.close()

    return render_template("editar.html", admin=admin)




# Home (si está logueado)
@app.route("/")
def logueado():


    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3030, debug=True)

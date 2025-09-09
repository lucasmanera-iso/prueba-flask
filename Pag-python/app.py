from flask import Flask, render_template, request
import pymysql

app = Flask(__name__)

# Función para conectar a MySQL con PyMySQL
def get_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="1233",
            database="app_python",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Conectado correctamente a MySQL con PyMySQL")
        return connection
    except pymysql.MySQLError as err:
        print(f"❌ Error al conectar con MySQL: {err}")
        return None

# Ruta principal
@app.route("/", methods=["GET", "POST"])
def register():
    mensaje = ""
    if request.method == "POST":
        nombre = request.form.get("Nombre")
        email = request.form.get("Email")
        password = request.form.get("password")

        conn = get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    query = "INSERT INTO usuarios (Nombre, Email, Contraseña) VALUES (%s, %s, %s)"
                    cursor.execute(query, (nombre, email, password))
                    conn.commit()
                mensaje = "✅ Usuario registrado correctamente!"
            except pymysql.MySQLError as err:
                mensaje = f"❌ Error al insertar en MySQL: {err}"
            finally:
                conn.close()
        else:
            mensaje = "❌ Error de conexión con la base de datos."

    return render_template("register.html", mensaje=mensaje)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3030, debug=True)
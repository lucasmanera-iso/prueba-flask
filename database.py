import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="1233",
        database="app_python"
    )
    print("✅ Conectado correctamente con PyMySQL")
    conn.close()
except pymysql.MySQLError as e:
    print("❌ Error:", e)
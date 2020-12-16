import mariadb

def connect_to_db():
    try:
        conn = mariadb.connect(
            user="*",
            password="*",
            host="*",
            port=3306,
            database="*"
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        conn.exit(1)
    # Get Cursor
    cursor = conn.cursor()
    return conn,cursor

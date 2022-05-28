import mariadb

def connect_to_db():
    try:
        conn = mariadb.connect(
            user="xuxlffke_scraperuser",
            password="lA,wA&5$w]}=",
            host="88.99.136.47",
            port=3306,
            database="xuxlffke_scrapingdb_final"
        )
        conn.autocommit = True
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        conn.exit(1)
    # Get Cursor
    cursor = conn.cursor()

    return conn,cursor
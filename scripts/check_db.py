from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')) if os.getenv('DB_PORT') else None,
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME'),
        connection_timeout=5
    )
    print('CONNECTED' if conn.is_connected() else 'NOT_CONNECTED')
    conn.close()
except Exception as e:
    print('ERROR:', e)
